import unittest

from ddb_single.table import FieldType, Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

import datetime

import logging

logging.basicConfig(level=logging.DEBUG)

table = Table(
    table_name="query_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
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

    def test_search(self):
        res = query.model(User).search(User.name.eq("test1"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test1")

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
        self.assertEqual(len(res), 3)

    def test_not_equal(self):
        res = query.model(User).search(User.name.ne("test1"))
        self.assertEqual(len(res), 2)

    def test_begins(self):
        res = query.model(User).search(User.name.begins_with("test"))
        self.assertEqual(len(res), 3)
