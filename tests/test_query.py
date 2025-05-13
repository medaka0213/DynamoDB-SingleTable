import unittest
from unittest.mock import patch, MagicMock
from ddb_single.table import FieldType, Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from ddb_single.error import ValidationError

import datetime
import logging

logging.basicConfig(level=logging.INFO)

table = Table(
    table_name="query_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    endpoint_url="http://localhost:8000",
    region_name="us-west-2",
    aws_access_key_id="fakeMyKeyId",
    aws_secret_access_key="fakeSecretAccessKey",
)
table.init()


class User(BaseModel):
    __table__ = table
    __model_name__ = "user"
    name = DBField(unique_key=True, nullable=False)
    name_ignore_case = DBField(search_key=True, ignore_case=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description = DBField()
    config = DBField(type=FieldType.MAP)
    tag_list = DBField(type=FieldType.LIST)


query = Query(table)

print("table_name:", table.__table_name__)


class TestCRUD(unittest.TestCase):
    def setUp(self):
        test1 = User(
            name="test",
            name_ignore_case="Test",
            email="",
            age=20,
            config={"a": 1, "b": 2},
            tag_list=["tag1", "tag2"],
        )
        test2 = User(
            pk="user_test2",
            name="test2",
            email=None,
            name_ignore_case="Test2",
            tag_list=[],
        )
        test3 = User(
            pk="user_test3",
            name="test3",
            name_ignore_case="Test3",
        )
        query.model(test1).create()
        query.model(test2).create()
        query.model(test3).create()
        # 効果確認
        res = query.model(User).get(test1.data["pk"])
        self.assertIsNotNone(res)
        self.assertEqual(res["pk"], test1.data["pk"])
        self.assertEqual(res["sk"], test1.data["sk"])
        self.assertEqual(res["name"], test1.data["name"])
        self.assertEqual(res["age"], test1.data["age"])
        self.assertEqual(res["config"]["a"], test1.data["config"]["a"])
        self.assertEqual(res["config"]["b"], test1.data["config"]["b"])
        self.assertEqual(res["tag_list"], test1.data["tag_list"])

        super().setUp()

    def test_01_create_validation_error(self):
        with self.assertRaises(ValidationError):
            test1 = User(
                name=None,
                name_ignore_case="Test Validation Error",
                email="",
                age=20,
                config={"a": 1, "b": 2},
            )
            query.model(test1).create()
        res = query.model(User).search(
            User.name_ignore_case.eq("Test Validation Error")
        )
        self.assertEqual(len(res), 0)

    def test_02_0_search(self):
        res = query.model(User).search(User.name.eq("test"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test")

    def test_02_1_0_search_by_get_field(self):
        """Search by get_field"""
        res = query.model(User).search(
            User(__skip_validation__=True).get_field("name").eq("test")
        )
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test")

    def test_02_1_1_search_by_get_field_not_found(self):
        """Search by get_field: not found"""
        res = query.model(User).search(
            User(__skip_validation__=True).get_field("name").eq("Test")
        )
        self.assertEqual(len(res), 0)

    def test_02_2_get_by_unique(self):
        res = query.model(User).get_by_unique("test")
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "test")

    def test_02_3_0_search_ignore_case(self):
        """Search ignoring case"""
        res = query.model(User).search(User.name_ignore_case.eq("test"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name_ignore_case"], "Test")

        res = query.model(User).search(User.name_ignore_case.in_(["test"]))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name_ignore_case"], "Test")

    def test_02_3_1_search_ignore_case_found_if_uppercase(self):
        """Search ignoring case: found if uppercase"""
        res = query.model(User).search(User.name_ignore_case.eq("TEST"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name_ignore_case"], "Test")

    def test_02_3_2_search_ignore_case_not_found(self):
        """Search ignoring case: not found"""
        res = query.model(User).search(User.name_ignore_case.eq("NOTFOUND"))
        self.assertEqual(len(res), 0)

    def test_03_01_update(self):
        """Update by primary key: query.model(payload).update()"""
        test = query.model(User).get_by_unique("test")
        test["age"] = 30
        new_test = User(**test)
        query.model(new_test).update()
        # 効果確認
        res = query.model(User).get_by_unique("test")
        self.assertEqual(res["age"], 30)
        # 二重投稿になってないか確認
        res = query.model(User).search(User.name.eq("test"))
        self.assertEqual(len(res), 1)

    def test_03_01_update_validation_error(self):
        """Update by primary key: query.model(payload).update() on validation error"""
        test = query.model(User).get_by_unique("test")
        with self.assertRaises(ValidationError):
            test["name"] = None
            new_test = User(**test)
            query.model(new_test).update()

    def test_03_02_update(self):
        """Update by primary key: query.model(payload).update(target)"""
        test = query.model(User).get_by_unique("test")
        query.model(User(**test)).update({"age": 40, "email": "test@example.com"})
        # 効果確認
        res = query.model(User).get_by_unique("test")
        self.assertEqual(res["age"], 40)
        self.assertEqual(res["email"], "test@example.com")
        # 二重投稿になってないか確認
        res = query.model(User).search(User.name.eq("test"))
        self.assertEqual(len(res), 1)

    def test_03_02_update_validation_error(self):
        """Update by primary key: query.model(payload).update(target) on validation error"""
        test = query.model(User).get_by_unique("test")
        with self.assertRaises(ValidationError):
            query.model(User(**test)).update({"name": None})

    def test_03_03_update_empty(self):
        """Update by primary key: query.model(payload).update(target)"""
        test = query.model(User).get_by_unique("test")
        query.model(User(**test)).update({"email": ""})
        # 効果確認
        res = query.model(User).get_by_unique("test")
        self.assertEqual(res["email"], "")
        # 二重投稿になってないか確認
        res = query.model(User).search(User.name.eq("test"))
        self.assertEqual(len(res), 1)

    def test_04_delete(self):
        query.model(User).delete_by_unique("test")
        # 効果確認
        res = query.model(User).search(User.name.eq("test"))
        self.assertEqual(len(res), 0)

        # 存在しないデータを削除しようとした場合 (エラーにならない)
        query.model(User).delete_by_unique("test")

    def test_04_02_delete_by_pk(self):
        # 対象データが存在することを確認
        res = query.model(User).search(User.name.eq("test2"))
        self.assertEqual(len(res), 1)
        # 削除
        query.model(User).delete_by_pk("user_test2")
        # 効果確認
        res = query.model(User).search(User.name.eq("test2"))
        self.assertEqual(len(res), 0)

        # 存在しないデータを削除しようとした場合 (エラーにならない)
        query.model(User).delete_by_pk("user_test2")

    @patch("ddb_single.query.Query.delete_by_pk")
    def test_04_03_delete_by_pk_2(self, mock_delete_by_pk: MagicMock):
        """Delete by primary key: query.model(payload).delete()"""
        # 対象データが存在することを確認
        res = query.model(User).search(User.name.eq("test3"))
        self.assertEqual(len(res), 1)
        # 削除
        query.model(User(**res[0])).delete()
        # 効果確認
        mock_delete_by_pk.assert_called_once_with("user_test3", batch=None)

    @patch("ddb_single.query.Query.delete_by_unique")
    def test_04_03_delete_by_unique_2(self, mock_delete_by_unique: MagicMock):
        """Delete by unique key: query.model(payload).delete()"""
        # 対象データが存在することを確認
        res = query.model(User).search(User.name.eq("test3"))
        self.assertEqual(len(res), 1)
        # 削除
        query.model(User(name="test3")).delete()
        # 効果確認
        mock_delete_by_unique.assert_called_once_with("test3", batch=None)


class SimpleModel(BaseModel):
    __table__ = table
    __model_name__ = "simple"
    # nullable=True, default=None, default_factory=None の場合に
    # 前回の値が残っていないことを確認
    name = DBField(unique_key=True, nullable=False)
    optional_field = DBField(nullable=True)


class TestValueReuse(unittest.TestCase):
    def test_optional_field_not_reused_across_instances(self):
        # 1回目は値を渡す
        first = SimpleModel(name="test-1", optional_field="first_value")
        self.assertEqual(first.data["optional_field"], "first_value")

        # 2回目は値を渡さない → None を期待
        second = SimpleModel(name="test-1")
        self.assertIsNone(
            second.data["optional_field"],
            "optional_field が前回の 'first_value' を使い回しています",
        )


if __name__ == "__main__":
    unittest.main()
