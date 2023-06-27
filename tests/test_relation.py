import unittest

from ddb_single.table import FieldType, Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

import datetime

table = Table(
    table_name="rel_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    endpoint_url="http://localhost:8000",
    region_name="us-west-2",
    aws_access_key_id="ACCESS_ID",
    aws_secret_access_key="ACCESS_KEY",
)
table.init()


class User(BaseModel):
    __table__ = table
    __model_name__ = "user"
    name = DBField(unique_key=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description = DBField()


class BlogPost(BaseModel):
    __model_name__ = "blogpost"
    __table__ = table
    title = DBField(unique_key=True)
    content = DBField(search_key=True)
    author = DBField(reletion=User)


print("table_name:", table.__table_name__)
query = Query(table)


class TestRelation(unittest.TestCase):
    def setUp(self) -> None:
        self.user = User(name="test", age=20)
        query.model(self.user).create()
        return super().setUp()

    def test_01_create(self):
        blogpost = BlogPost(title="test", content="test", author=self.user)
        query.model(blogpost).create()
        # 効果確認
        res = query.model(BlogPost).get(blogpost.data["pk"])
        self.assertIsNotNone(res)
        self.assertEqual(res["author"], self.user.data["name"])

    def test_02_0_get_rel(self):
        blogpost = query.model(BlogPost).search(BlogPost.title.eq("test"))
        self.assertEqual(len(blogpost), 1)

        # モデルから検索
        blogpost = BlogPost(**blogpost[0])
        res = query.model(blogpost).get_relation(model=User)
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test")
        # フィールドから検索
        res = query.model(blogpost).get_relation(field=BlogPost.author)
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test")

    def test_02_0_get_ref(self):
        res = query.model(self.user).get_reference(model=BlogPost)
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "test")
        # フィールドから検索
        res = query.model(self.user).get_reference(field=BlogPost.author)
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "test")

    def test_03_update(self):
        new_user = User(name="test2", age=20)
        query.model(new_user).create()
        res = query.model(User).search(User.name.eq("test2"))
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test2")

        # MessageのUserを更新
        blogpost = query.model(BlogPost).search(BlogPost.title.eq("test"))
        self.assertEqual(len(blogpost), 1)
        blogpost = blogpost[0]
        blogpost["author"] = new_user
        blogpost = BlogPost(**blogpost)
        query.model(blogpost).update()
        # 効果確認
        res = query.model(BlogPost).get(blogpost.data["pk"])
        self.assertIsNotNone(res)
        self.assertEqual(res["author"], "test2")
        # 効果確認 (関連)
        rel_user = query.model(blogpost).get_relation(model=User)
        self.assertEqual(len(rel_user), 1)
        self.assertEqual(rel_user[0]["name"], "test2")
