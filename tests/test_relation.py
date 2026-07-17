import logging
import unittest

from ddb_single.error import NotFoundError
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from ddb_single.table import FieldType
from tests.conftest import make_table

logging.basicConfig(level=logging.INFO)

table = make_table("rel_test_")
table.init()


class User(BaseModel):
    __table__ = table
    __model_name__ = "user"
    name = DBField(unique_key=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description = DBField()


class Image(BaseModel):
    __table__ = table
    __model_name__ = "image"
    unique = DBField(unique_key=True)
    title = DBField(search_key=True)


class Slide(BaseModel):
    __table__ = table
    __model_name__ = "slide"
    unique = DBField(unique_key=True)
    name = DBField(search_key=True)
    user = DBField(relation=User, search_key=True)
    pdf = DBField(relation=Image, search_key=True)
    markdown = DBField(relation=Image, search_key=True)


class BlogPost(BaseModel):
    __model_name__ = "blogpost"
    __table__ = table
    title = DBField(unique_key=True)
    content = DBField(search_key=True)
    author = DBField(relation=User)


class Comment(BaseModel):
    __model_name__ = "comment"
    __table__ = table
    title = DBField(unique_key=True)
    content = DBField(search_key=True)
    author = DBField(relation=User, relation_raise_if_not_found=True)


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
        # 引数なし
        res = query.model(blogpost).get_relation()
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
        # 引数なし
        res = query.model(self.user).get_reference()
        self.assertIsNotNone(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "test")

    def test_03_update(self):
        """アイテム更新 正常系"""

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

    def test_04_non_exist(self):
        """アイテム更新 存在しないユーザーを指定した場合、関連が削除されることを確認するテスト"""

        # MessageのUserを更新
        blogpost = query.model(BlogPost).search(BlogPost.title.eq("test"))
        self.assertEqual(len(blogpost), 1)
        blogpost = blogpost[0]
        blogpost["author"] = "user_not_exist"
        blogpost = BlogPost(**blogpost)
        query.model(blogpost).update()
        # 効果確認
        res = query.model(BlogPost).get(blogpost.data["pk"])
        self.assertIsNotNone(res)
        self.assertEqual(res["author"], "user_not_exist")
        # 効果確認 (関連は削除される)
        rel_user = query.model(blogpost).get_relation(model=User)
        self.assertEqual(len(rel_user), 0)

    def test_04_non_exist_raise(self):
        """アイテム更新 存在しないユーザーを指定した場合、例外が発生することを確認するテスト"""

        # Blo
        with self.assertRaises(NotFoundError):
            comment = Comment(unique_key="test", content="test", author="user_not_exist")
            query.model(comment).update()

    def test_05_multiple_relations(self):
        """複数の関連フィールドを持つモデルのテスト - Slideモデルのような複雑なケース"""

        # Create related items
        user = User(name="slide_user", age=25)
        query.model(user).create()

        pdf_image = Image(unique="pdf-image-1", title="PDF Image")
        query.model(pdf_image).create()

        markdown_image = Image(unique="markdown-image-1", title="Markdown Image")
        query.model(markdown_image).create()

        # Create slide with multiple relations
        slide = Slide(
            unique="test-slide-1",
            name="Test Slide",
            user=user,
            pdf=pdf_image,
            markdown=markdown_image,
        )
        query.model(slide).create()

        # Verify slide was created
        res = query.model(Slide).get(slide.data["pk"])
        self.assertIsNotNone(res)
        self.assertEqual(res["unique"], "test-slide-1")
        self.assertEqual(res["user"], "slide_user")
        self.assertEqual(res["pdf"], "pdf-image-1")
        self.assertEqual(res["markdown"], "markdown-image-1")

        # Verify relations were created - User relation
        user_relations = query.model(slide).get_relation(model=User)
        self.assertEqual(len(user_relations), 1, "Should have 1 User relation")
        self.assertEqual(user_relations[0]["name"], "slide_user")

        # Verify relations were created - Image relations
        image_relations = query.model(slide).get_relation(model=Image)
        self.assertEqual(len(image_relations), 2, "Should have 2 Image relations (pdf + markdown)")

        # Verify we can find the slide from the user
        user_refs = query.model(user).get_reference(model=Slide)
        self.assertEqual(len(user_refs), 1, "User should reference 1 Slide")
        self.assertEqual(user_refs[0]["unique"], "test-slide-1")

        # Verify we can find the slide from the images
        pdf_refs = query.model(pdf_image).get_reference(model=Slide)
        self.assertEqual(len(pdf_refs), 1, "PDF Image should reference 1 Slide")
        self.assertEqual(pdf_refs[0]["unique"], "test-slide-1")

        markdown_refs = query.model(markdown_image).get_reference(model=Slide)
        self.assertEqual(len(markdown_refs), 1, "Markdown Image should reference 1 Slide")
        self.assertEqual(markdown_refs[0]["unique"], "test-slide-1")


if __name__ == "__main__":
    unittest.main()
