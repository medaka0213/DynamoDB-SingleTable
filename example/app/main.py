"""ddb_single を使った Single-Table Design ブログアプリのサンプル (FastAPI)。"""

import datetime
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from models import Comment, Post, User, table

from ddb_single import Query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

query = Query(table)
templates = Jinja2Templates(directory="templates")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _wait_for_dynamodb(retries: int = 30, interval: float = 1.0) -> None:
    """DynamoDB Local の起動を待ってからテーブルを初期化する。"""
    for attempt in range(1, retries + 1):
        try:
            table.init()
            logger.info("table '%s' is ready", table.__table_name__)
            return
        except Exception:
            logger.info("waiting for DynamoDB... (%d/%d)", attempt, retries)
            time.sleep(interval)
    raise RuntimeError("DynamoDB Local に接続できませんでした")


def _seed_data() -> None:
    """初回起動時にサンプルデータを投入する。"""
    if query.model(Post).search(pk_only=True):
        return
    logger.info("seeding sample data...")
    alice = User(name="Alice", email="alice@example.com", bio="ネコとサーバーレスが好き。")
    bob = User(name="Bob", email="bob@example.com", bio="DynamoDB を勉強中。")
    query.model(alice).create()
    query.model(bob).create()

    posts = [
        Post(
            slug=uuid.uuid4().hex[:12],
            title="Single-Table Design 入門",
            content="DynamoDB では複数のエンティティを 1 つのテーブルに格納する設計が有効です。\n"
            "このアプリでは User / Post / Comment がすべて同じテーブルに入っています。\n"
            "dynamodb-admin (ポート 8001) で実際のアイテム構造を覗いてみてください。",
            author=alice,
            created_at=_now(),
        ),
        Post(
            slug=uuid.uuid4().hex[:12],
            title="ddb_single の検索キー",
            content="search_key=True を付けたフィールドは search_* という検索用アイテムとして\n"
            "GSI にインデックスされ、eq / contains / begins_with などで検索できます。",
            author=bob,
            created_at=_now(),
        ),
    ]
    for post in posts:
        query.model(post).create()

    comment = Comment(
        comment_id=uuid.uuid4().hex,
        body="リレーションは rel_ プレフィックスのアイテムで表現されるんですね!",
        author_name="Bob",
        post=posts[0],
        created_at=_now(),
    )
    query.model(comment).create()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _wait_for_dynamodb()
    if os.environ.get("SEED_DATA") == "1":
        _seed_data()
    yield


app = FastAPI(title="ddb_single blog example", lifespan=lifespan)


def _sorted_posts(posts: list[dict]) -> list[dict]:
    return sorted(posts, key=lambda p: p.get("created_at") or "", reverse=True)


@app.get("/")
def index(request: Request, q: str = ""):
    if q:
        posts = query.model(Post).search(Post.title.contains(q))
    else:
        posts = query.model(Post).search()
    return templates.TemplateResponse(request, "index.html", {"posts": _sorted_posts(posts), "q": q})


@app.get("/posts/new")
def new_post(request: Request):
    authors = query.model(User).search()
    return templates.TemplateResponse(request, "post_form.html", {"authors": authors})


@app.post("/posts")
def create_post(
    title: str = Form(...),
    content: str = Form(...),
    author_name: str = Form(...),
):
    author_name = author_name.strip()
    if not title.strip() or not author_name:
        raise HTTPException(status_code=400, detail="タイトルと著者名は必須です")

    # 著者が未登録なら作成 (name が unique_key なので既存なら再利用される)
    author_data = query.model(User).get_by_unique(author_name)
    if author_data:
        author = User(**author_data)
    else:
        author = User(name=author_name)
        query.model(author).create()

    post = Post(
        slug=uuid.uuid4().hex[:12],
        title=title.strip(),
        content=content,
        author=author,
        created_at=_now(),
    )
    query.model(post).create()
    return RedirectResponse(f"/posts/{post.data['pk']}", status_code=303)


@app.get("/posts/{pk}")
def post_detail(request: Request, pk: str):
    post_data = query.model(Post).get(pk)
    if not post_data:
        raise HTTPException(status_code=404, detail="記事が見つかりません")
    post = Post(**post_data)

    # リレーション: Post -> User (著者)
    authors = query.model(post).get_relation(field=Post.author)
    # 逆参照 (reference): この Post を参照している Comment 一覧
    comments = query.model(post).get_reference(field=Comment.post)
    comments.sort(key=lambda c: c.get("created_at") or "")

    return templates.TemplateResponse(
        request,
        "post_detail.html",
        {
            "post": post_data,
            "author": authors[0] if authors else None,
            "comments": comments,
        },
    )


@app.post("/posts/{pk}/comments")
def add_comment(pk: str, author_name: str = Form(""), body: str = Form(...)):
    post_data = query.model(Post).get(pk)
    if not post_data:
        raise HTTPException(status_code=404, detail="記事が見つかりません")
    comment = Comment(
        comment_id=uuid.uuid4().hex,
        body=body,
        author_name=author_name.strip() or "名無しさん",
        post=Post(**post_data),
        created_at=_now(),
    )
    query.model(comment).create()
    return RedirectResponse(f"/posts/{pk}", status_code=303)


@app.post("/posts/{pk}/delete")
def delete_post(pk: str):
    post_data = query.model(Post).get(pk)
    if not post_data:
        raise HTTPException(status_code=404, detail="記事が見つかりません")
    post = Post(**post_data)

    # 記事にぶら下がるコメントもまとめて削除
    comments = query.model(post).get_reference(field=Comment.post, pk_only=True)
    with table.batch_writer() as batch:
        for comment_pk in comments:
            query.model(Comment).delete_by_pk(comment_pk, batch=batch)
    query.model(Post).delete_by_pk(pk)
    return RedirectResponse("/", status_code=303)


@app.get("/authors")
def authors(request: Request):
    users = query.model(User).search()
    users.sort(key=lambda u: u.get("name") or "")
    return templates.TemplateResponse(request, "authors.html", {"authors": users})


@app.get("/authors/{pk}")
def author_detail(request: Request, pk: str):
    user_data = query.model(User).get(pk)
    if not user_data:
        raise HTTPException(status_code=404, detail="著者が見つかりません")
    user = User(**user_data)
    # 逆参照: この User を author に持つ Post 一覧
    posts = query.model(user).get_reference(field=Post.author)
    return templates.TemplateResponse(
        request,
        "author_detail.html",
        {"author": user_data, "posts": _sorted_posts(posts)},
    )
