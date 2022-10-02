import unittest
import asyncio

from ddb_single.table import FieldType, Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

table = Table(
    table_name="test",
    endpoint_url="http://localhost:8000",
)
table.init()

class Test(BaseModel):
    __table__=table
    __model_name__ = "user"
    pk = DBField(primary_key=True)
    sk = DBField(secondary_key=True)
    name = DBField(unique_key=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description=DBField()

query = Query(table)

class Sample(unittest.TestCase):
    def test_create(self):
        test = Test(unique="test", name="test", age=20)
        print("test", test)
        query.model(test).create()

    def test_get(self):
        print(query.model(Test).search(Test.name.eq("test")))
        print(query.model(Test).get_by_unique("test"))

    def test_update(self):
        test = Test(unique="test", name="test", age=20)
        print("test", test.data)
        query.model(test).update()

    def test_delete(self):
        query.model(Test).delete_by_unique("test")
