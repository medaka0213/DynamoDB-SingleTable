import unittest
import asyncio

from ddb_single.table import Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

table = Table(
    table_name="test",
    endpoint_url="http://localhost:8000",
)
table.init()

class Test(BaseModel):
    __table__=table
    __model_name__ = "testmodel"
    pk = DBField(primary_key=True)
    sk = DBField(secondary_key=True)
    unique = DBField(unique_key=True)
    name = DBField(search_key=True)
    attr = DBField()

query = Query(table)

class Sample(unittest.TestCase):
    def test_create(self):
        test = Test(unique="test", name="test", attr="test")
        print("test", test)
        query.model(test).create()

    def test_get(self):
        print(query.model(Test).search(Test.name.eq("test")))
        print(query.model(Test).get_by_unique("test"))

    def test_update(self):
        test = Test(unique="test", name="test", attr="test")
        print("test", test.data)
        query.model(test).update()

    def test_delete(self):
        query.model(Test).delete_by_unique("test")
