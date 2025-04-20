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
    name_ignore_nase = DBField(search_key=True, ignore_case=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description = DBField()
    config = DBField(type=FieldType.MAP)
    tag_list = DBField(type=FieldType.LIST)


query = Query(table)

print("table_name:", table.__table_name__)


class TestCRUD(unittest.TestCase):
    def test_01_create(self):
        test1 = User(
            name="test",
            name_ignore_nase="Test",
            email="",
            age=20,
            config={"a": 1, "b": 2},
            tag_list=["tag1", "tag2"],
        )
        test2 = User(
            pk="user_test2",
            name="test2",
            email=None,
            name_ignore_nase="Test2",
            tag_list=[],
        )
        test3 = User(
            pk="user_test3",
            name="test3",
            name_ignore_nase="Test3",
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

    def test_01_create_validation_error(self):
        with self.assertRaises(ValidationError):
            test1 = User(
                name=None,
                name_ignore_nase="Test Valudation Error",
                email="",
                age=20,
                config={"a": 1, "b": 2},
            )
            query.model(test1).create()
        res = query.model(User).search(
            User.name_ignore_nase.eq("Test Valudation Error")
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
        res = query.model(User).search(User.name_ignore_nase.eq("test"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name_ignore_nase"], "Test")

    def test_02_3_1_search_ignore_case_found_if_uppercase(self):
        """Search ignoring case: found if uppercase"""
        res = query.model(User).search(User.name_ignore_nase.eq("TEST"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name_ignore_nase"], "Test")

    def test_02_3_2_search_ignore_case_not_found(self):
        """Search ignoring case: not found"""
        res = query.model(User).search(User.name_ignore_nase.eq("NOTFOUND"))
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

    def test_04_02_delete_by_pk(self):
        # 対象データが存在することを確認
        res = query.model(User).search(User.name.eq("test2"))
        self.assertEqual(len(res), 1)
        # 削除
        query.model(User).delete_by_pk("user_test2")
        # 効果確認
        res = query.model(User).search(User.name.eq("test2"))
        self.assertEqual(len(res), 0)

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


if __name__ == "__main__":
    unittest.main()
