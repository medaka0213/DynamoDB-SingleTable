# ddb_single サンプルアプリ: ブログ

`ddb_single` (DynamoDB Single-Table Design ライブラリ) を使ったブログアプリのサンプルです。
FastAPI + DynamoDB Local で構成され、docker compose だけで起動できます。

User (著者) / Post (記事) / Comment (コメント) の 3 モデルが **1 つの DynamoDB テーブル** に格納されます。

## 起動方法

```bash
cd example
docker compose up --build
```

| サービス | URL | 説明 |
|-|-|-|
| ブログアプリ | http://localhost:8080 | FastAPI + Jinja2 の Web UI |
| dynamodb-admin | http://localhost:8001 | テーブルの中身 (single-table の実アイテム) を確認できる管理画面 |
| DynamoDB Local | http://localhost:8000 | DynamoDB エンドポイント |

ポートが埋まっている場合は環境変数で変更できます:

```bash
APP_PORT=18080 ADMIN_PORT=18001 DYNAMODB_PORT=18000 docker compose up --build
```

初回起動時にサンプルデータが自動投入されます (無効にするには `docker-compose.yml` の `SEED_DATA` を `"0"` に)。

## データモデル

```python
class User(BaseModel):
    __model_name__ = "user"
    name = DBField(unique_key=True)      # ユニークキー: 同名なら同一著者として扱う
    email = DBField(search_key=True)     # GSI で検索可能
    bio = DBField()

class Post(BaseModel):
    __model_name__ = "post"
    slug = DBField(unique_key=True)      # uuid から自動生成
    title = DBField(search_key=True)     # タイトル検索 (contains) に使用
    content = DBField()
    author = DBField(relation=User)      # User へのリレーション
    created_at = DBField(search_key=True)

class Comment(BaseModel):
    __model_name__ = "comment"
    comment_id = DBField(unique_key=True)
    body = DBField()
    author_name = DBField()
    post = DBField(relation=Post)        # Post へのリレーション
    created_at = DBField()
```

## このサンプルで使っている ddb_single の機能

| 機能 | 使用箇所 (`app/main.py`) |
|-|-|
| `query.model(post).create()` | 記事・コメント・著者の作成 |
| `query.model(Post).search()` | 記事一覧の取得 |
| `query.model(Post).search(Post.title.contains(q))` | タイトル検索 |
| `query.model(User).get_by_unique(name)` | 著者名からの取得 (未登録なら新規作成) |
| `query.model(post).get_relation(field=Post.author)` | 記事 → 著者 (リレーション) |
| `query.model(post).get_reference(field=Comment.post)` | 記事 ← コメント (逆参照) |
| `query.model(user).get_reference(field=Post.author)` | 著者 ← 記事 (逆参照) |
| `table.batch_writer()` + `delete_by_pk(batch=...)` | 記事削除時にコメントを一括削除 |

## テーブルの中身を覗く

single-table design の面白いところは、1 テーブルに複数種類のアイテムが同居する点です。
http://localhost:8001 (dynamodb-admin) で `blog_example` テーブルを開くと、次のようなアイテムが見えます:

| pk | sk | 説明 |
|-|-|-|
| `user_xxxx` | `user_item` | 著者本体 |
| `user_xxxx` | `search_user_name` | 著者名の検索用アイテム |
| `post_xxxx` | `post_item` | 記事本体 |
| `post_xxxx` | `search_post_title` | タイトル検索用アイテム |
| `post_xxxx` | `rel_user_xxxx` | 記事 → 著者のリレーションアイテム |
| `comment_xxxx` | `rel_post_xxxx` | コメント → 記事のリレーションアイテム |

## E2E テスト (Playwright)

`example/e2e/` に Playwright による E2E テストがあります。
CI では単体テスト通過後にこのサンプルを docker compose で起動し、自動実行されます。

ローカルで実行する場合:

```bash
# リポジトリルートで
uv sync --group e2e
uv run playwright install chromium

# サンプルアプリを起動 (healthcheck 完了まで待機)
docker compose -f example/docker-compose.yml up -d --build --wait

# E2E テスト実行 (接続先は E2E_BASE_URL で変更可)
uv run pytest example/e2e -v
```

## ローカル (Docker なし) で動かす場合

```bash
# リポジトリルートで
uv sync
docker compose up -d          # DynamoDB Local (ポート 8000) だけ起動
cd example/app
uv run --with fastapi --with "uvicorn[standard]" --with jinja2 --with python-multipart \
    uvicorn main:app --reload --port 8080
```
