import unittest
from ddb_single.table import Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

import datetime
import logging

logging.basicConfig(level=logging.INFO)

table = Table(
    table_name="query_unique_doubled_test_"
    + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
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
    email = DBField(unique_key=True)
    description = DBField()


query = Query(table)

print("table_name:", table.__table_name__)


class TestUniqueDoubled(unittest.TestCase):
    def test_01_create(self):
        test1 = User(
            name="test1",
            email="test1@example.com",
        )
        test2 = User(
            name="test2",
            email="test2@example.com",
        )
        test3 = User(
            name="test3",
            email="test3@example.com",
        )
        query.model(test1).create()
        query.model(test2).create()
        query.model(test3).create()

    def test_02_get_by_unique(self):
        res = query.model(User).get_by_unique("test1")
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "test1")

        res = query.model(User).get_by_unique("test1@example.com")
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "test1")

    def test_02_get_batch(self):
        """キーのリストから一括取得"""
        # ユニークキーから取得
        res = query.model(User).batch_get_by_unique(["test1", "test2@example.com"])
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["name"], "test1")
        self.assertEqual(res[1]["name"], "test2")
        # プライマリキーから取得
        res = query.model(User).batch_get([x["pk"] for x in res])
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["name"], "test1")
        self.assertEqual(res[1]["name"], "test2")

    def test_02_get_by_unique_keys_specified(self):
        res = query.model(User).get_by_unique("test1@example.com", keys=[User.name])
        self.assertIsNone(res)

        res = query.model(User).get_by_unique("test1@example.com", keys=[User.email])
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "test1")

    def test_02_get_by_unique_keys_specified_by_string(self):
        res = query.model(User).get_by_unique("test1@example.com", keys=["name"])
        self.assertIsNone(res)

        res = query.model(User).get_by_unique("test1@example.com", keys=["email"])
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "test1")


if __name__ == "__main__":
    unittest.main()
