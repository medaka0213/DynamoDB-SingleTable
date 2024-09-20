import unittest

from ddb_single.table import FieldType, Table, Key, Attr
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
import ddb_single.utils_botos as util_b

import datetime
import logging

logging.basicConfig(level=logging.INFO)

table = Table(
    table_name="table_search_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
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


class TestSearchTable(unittest.TestCase):
    def setUp(self):
        for i in range(500):
            test = User(
                name=f"test{str(i).zfill(3)}",
                age=i,
                description=f"test description {'odd' if i % 2 == 0 else 'even'}_{i}",)
            query.model(test).create()
        test = UserNotFound(name="testNotFound")
        query.model(test).create()

    def test_search_staged_single(self):
        """STAGED"""
        searchEx = [{
            "FilterStatus": util_b.FilterStatus.STAGED,
            "IndexName": table.__search_index__,
            "KeyConditionExpression": Key("sk").eq("search_user_name") & Key("data").eq("test001"),
        }]
        res = table.search("user", *searchEx)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test001")

        # pk_only
        res = table.search("user", *searchEx, pk_only=True)
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], str)

    def test_search_staged_double(self):
        """STAGED複数"""
        searchEx = [{
            "FilterStatus": util_b.FilterStatus.STAGED,
            "IndexName": table.__search_index__,
            "KeyConditionExpression": Key("sk").eq("search_user_name") & Key("data").begins_with("test1"),
        }, {
            "FilterStatus": util_b.FilterStatus.STAGED,
            "IndexName": table.__search_num_index__,
            "KeyConditionExpression": Key("sk").eq("search_user_age") & Key("data-n").lte(15),
        }]
        res = table.search("user", *searchEx)
        self.assertEqual(len(res), 6)
        for r in res:
            self.assertLessEqual(r["age"], 15)
            self.assertTrue(r["name"].startswith("test1"))

        # pk_only
        res = table.search("user", *searchEx, pk_only=True)
        self.assertEqual(len(res), 6)
        for r in res:
            self.assertIsInstance(r, str)

    def test_search_staged_double_limit(self):
        """STAGED複数 + limit"""
        searchEx = [{
            "FilterStatus": util_b.FilterStatus.STAGED,
            "IndexName": table.__search_index__,
            "KeyConditionExpression": Key("sk").eq("search_user_name") & Key("data").begins_with("test1"),
        }, {
            "FilterStatus": util_b.FilterStatus.STAGED,
            "IndexName": table.__search_num_index__,
            "KeyConditionExpression": Key("sk").eq("search_user_age") & Key("data-n").lte(15),
        }]
        res = table.search("user", *searchEx, limit=3)
        self.assertEqual(len(res), 3)
        for r in res:
            self.assertLessEqual(r["age"], 15)
            self.assertTrue(r["name"].startswith("test1"))

        # pk_only
        res = table.search("user", *searchEx, pk_only=True, limit=3)
        self.assertEqual(len(res), 3)
        for r in res:
            self.assertIsInstance(r, str)

    def test_search_staged_filter(self):
        """STAGED + フィルタ"""
        searchEx = [{
            "FilterStatus": util_b.FilterStatus.STAGED,
            "IndexName": table.__search_index__,
            "KeyConditionExpression": Key("sk").eq("search_user_name") & Key("data").begins_with("test2"),
        }, {
            "FilterStatus": util_b.FilterStatus.FILTER,
            "FilterMethod": util_b.attr_method("description", "odd", util_b.QueryType.CONTAINS),
            "FilterExpression": Attr("description").contains("odd"),
        }]
        res = table.search("user", *searchEx)
        self.assertEqual(len(res), 5)
        for r in res:
            self.assertIn("odd", r["description"])
            self.assertTrue(r["name"].startswith("test2"))

        # pk_only
        res = table.search("user", *searchEx, pk_only=True)
        self.assertEqual(len(res), 5)
        for r in res:
            self.assertIsInstance(r, str)

    def test_search_filter(self):
        """フィルタ"""
        searchEx = [{
            "FilterStatus": util_b.FilterStatus.FILTER,
            "FilterMethod": util_b.attr_method("description", "odd", util_b.QueryType.CONTAINS),
            "FilterExpression": Attr("description").contains("odd"),
        }]
        res = table.search("user", *searchEx)
        self.assertEqual(len(res), 15)
        for r in res:
            self.assertIn("odd", r["description"])

        # pk_only
        res = table.search("user", *searchEx, pk_only=True)
        self.assertEqual(len(res), 15)
        for r in res:
            self.assertIsInstance(r, str)

    def test_search_all(self):
        """全件検索"""
        res = table.search("user")
        self.assertEqual(len(res), 30)

        # pk_only
        res = table.search("user", pk_only=True)
        self.assertEqual(len(res), 30)
        for r in res:
            self.assertIsInstance(r, str)

    def test_all_items(self):
        res = table.all_items()
        self.assertEqual(len(res), 500)

    def test_list_models(self):
        res = table.list_models()
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], {
            "table_name": "user",
            "count": 500,
        })
        self.assertEqual(res[1], {
            "table_name": "userNotFound",
            "count": 1,
        })


if __name__ == "__main__":
    unittest.main()
