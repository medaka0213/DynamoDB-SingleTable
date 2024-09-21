import unittest

from ddb_single.table import FieldType, Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

import datetime
import logging

logging.basicConfig(level=logging.INFO)

table = Table(
    table_name="search_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    endpoint_url="http://localhost:8000",
    region_name="us-west-2",
    aws_access_key_id="fakeMyKeyId",
    aws_secret_access_key="fakeSecretAccessKey",
)
table.init()


class User(BaseModel):
    __table__ = table
    __model_name__ = "user"
    name = DBField(unique_key=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description = DBField()


class UserNotFound(BaseModel):
    __table__ = table
    __model_name__ = "userNotFound"
    name = DBField(unique_key=True)


query = Query(table)

print("table_name:", table.__table_name__)


class TestSearch(unittest.TestCase):
    def setUp(self):
        test = User(name="test1", age=21)
        query.model(test).create()
        test = User(name="test2", age=22)
        query.model(test).create()
        test = User(name="test3", age=23)
        query.model(test).create()
        test = User(name="123", age=24)  # 数字の名前
        query.model(test).create()
        test = UserNotFound(name="testNotFound")
        query.model(test).create()

    def test_search(self):
        res = query.model(User).search(User.name.eq("test1"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test1")

    def test_search_num_as_str(self):
        res = query.model(User).search(User.name.eq(123))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "123")

    def test_search_str_as_num(self):
        res = query.model(User).search(User.age.eq("22"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["age"], 22)

    def test_get_by_unique(self):
        res = query.model(User).get_by_unique("test2")
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "test2")

    def test_search_by_get_field(self):
        res = query.model(User).search(User().get_field("name").eq("test3"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test3")

    def test_get_all(self):
        res = query.model(User).search()
        self.assertEqual(len(res), 4)
        self.assertIsInstance(res[0], dict)

    def test_not_equal(self):
        res = query.model(User).search(User.name.ne("test1"))
        self.assertEqual(len(res), 3)
        self.assertIsInstance(res[0], dict)

    def test_begins(self):
        res = query.model(User).search(User.name.begins_with("test"))
        self.assertEqual(len(res), 3)
        self.assertIsInstance(res[0], dict)

    def test_between(self):
        res = query.model(User).search(User.name.between("test1", "test2"))
        self.assertEqual(len(res), 2)
        self.assertIn(res[0]["name"], ["test1", "test2"])
        self.assertIn(res[1]["name"], ["test1", "test2"])

    def test_between_num_as_str(self):
        res = query.model(User).search(User.name.between(100, 200))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "123")

    def test_between_str_as_num(self):
        res = query.model(User).search(User.age.between("22", "24"))
        self.assertEqual(len(res), 3)
        self.assertIn(res[0]["age"], [22, 23, 24])
        self.assertIn(res[1]["age"], [22, 23, 24])

    def test_limit(self):
        res = query.model(User).search(limit=1)
        self.assertEqual(len(res), 1)
        self.assertIn(res[0]["name"], ["test1", "test2", "test3", "123"])

    def test_pk_only(self):
        res = query.model(User).search(
            User().get_field("name").eq("test3"), pk_only=True
        )
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], str)

    def test_pk_only_not_staged(self):
        res = query.model(User).search(pk_only=True)
        self.assertEqual(len(res), 4)
        self.assertIsInstance(res[0], str)

    def test_empty(self):
        with self.assertNoLogs(
            logger=logging.getLogger("ddb_single.table"), level=logging.ERROR
        ):
            res = query.model(User).search(User.name.eq(""))
            self.assertEqual(len(res), 0)


if __name__ == "__main__":
    unittest.main()
