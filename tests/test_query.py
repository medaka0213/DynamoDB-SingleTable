import unittest

from ddb_single.table import FieldType, Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

import datetime

table = Table(
    table_name="query_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    endpoint_url="http://localhost:8000",
)
table.init()

class User(BaseModel):
    __table__=table
    __model_name__ = "user"
    name = DBField(unique_key=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description=DBField()

query = Query(table)

print("table_name:", table.__table_name__)

class TestCRUD(unittest.TestCase):
    def test_01_create(self):
        test = User(
            name="test", 
            age=20
        )
        query.model(test).create()
        # 効果確認
        res = query.model(User).get(test.data["pk"])
        self.assertIsNotNone(res)
        self.assertEqual(res["pk"], test.data["pk"])
        self.assertEqual(res["sk"], test.data["sk"])

    def test_02_0_search(self):
        res = query.model(User).search(User.name.eq("test"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test")
    
    def test_02_1_get_by_unique(self):
        res = query.model(User).get_by_unique("test")
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "test")

    def test_03_update(self):
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

    def test_04_delete(self):
        query.model(User).delete_by_unique("test")
        # 効果確認
        res = query.model(User).search(User.name.eq("test"))
        self.assertEqual(len(res), 0)
