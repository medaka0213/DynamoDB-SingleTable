"""ブログアプリのデータモデル定義。

Single-Table Design なので、User / Post / Comment の 3 モデルすべてが
1 つの DynamoDB テーブルに格納される。
"""

import os

from ddb_single import BaseModel, DBField, Table

table = Table(
    table_name=os.environ.get("TABLE_NAME", "blog_example"),
    endpoint_url=os.environ.get("DYNAMODB_ENDPOINT_URL", "http://localhost:8000"),
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-west-2"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "fakeMyKeyId"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "fakeSecretAccessKey"),
)


class User(BaseModel):
    """著者。name をユニークキーとして識別する。"""

    __table__ = table
    __model_name__ = "user"

    name = DBField(unique_key=True)
    email = DBField(search_key=True)
    bio = DBField()


class Post(BaseModel):
    """ブログ記事。author は User へのリレーション。"""

    __table__ = table
    __model_name__ = "post"

    slug = DBField(unique_key=True)
    title = DBField(search_key=True)
    content = DBField()
    author = DBField(relation=User)
    created_at = DBField(search_key=True)


class Comment(BaseModel):
    """記事へのコメント。post は Post へのリレーション。"""

    __table__ = table
    __model_name__ = "comment"

    comment_id = DBField(unique_key=True)
    body = DBField()
    author_name = DBField()
    post = DBField(relation=Post)
    created_at = DBField()


# DBField の name などの内部属性は最初のインスタンス生成時に遅延初期化されるため、
# get_relation(field=Post.author) のようなフィールド指定をどのリクエストからでも
# 安全に使えるよう、起動時に各モデルを一度インスタンス化してセットアップしておく
for _model in (User, Post, Comment):
    _model()
