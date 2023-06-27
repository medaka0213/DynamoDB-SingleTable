import unittest

from ddb_single.table import FieldType, Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

import datetime

table = Table(
    table_name="batch_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
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
    age = DBField(FieldType.NUMBER)


query = Query(table)

print("table_name:", table.__table_name__)


class TestCRUD(unittest.TestCase):
    def test_01_create(self):
        with table.batch_writer() as batch:
            for i in range(10):
                user = User(name=f"test{i}", age=i)
                query.model(user).create(batch=batch)

        # 効果確認
        res = query.model(User).search(User.name.begins_with("test"), pk_only=True)
        self.assertEqual(len(res), 10)
        self.assertTrue(isinstance(res[0], str))
        res = query.model(User).search(User.name.begins_with("test"), pk_only=False)
        self.assertEqual(len(res), 10)
        self.assertTrue(isinstance(res[0], dict))

    def test_03_update(self):
        with table.batch_writer() as batch:
            for i in range(10):
                user = User(name=f"test{i}", age=i + 10)
                query.model(user).update(batch=batch)

        # 効果確認
        res = query.model(User).search(User.name.begins_with("test"))
        self.assertEqual(len(res), 10)
        self.assertTrue(isinstance(res[0], dict))
        for i in range(10):
            target = [x for x in res if x["name"] == f"test{i}"][0]
            self.assertEqual(target["age"], i + 10)

    def test_04_01_delete_by_unique(self):
        with table.batch_writer() as batch:
            for i in range(3):
                query.model(User).delete_by_unique(f"test{i}", batch=batch)
        # 効果確認
        res = query.model(User).search(User.name.begins_with("test"))
        self.assertEqual(len(res), 7)

    def test_04_02_delete(self):
        items = query.model(User).search(User.name.begins_with("test"))
        with table.batch_writer() as batch:
            for i in range(3):
                user = User(**items[i])
                query.model(user).delete(batch=batch)
        # 効果確認
        res = query.model(User).search(User.name.begins_with("test"))
        self.assertEqual(len(res), 4)

    def test_04_03_delete_by_pk(self):
        pks = query.model(User).search(User.name.begins_with("test"), pk_only=True)
        with table.batch_writer() as batch:
            for pk in pks[:3]:
                query.model(User).delete_by_pk(pk, batch=batch)
        # 効果確認
        res = query.model(User).search(User.name.begins_with("test"))
        self.assertEqual(len(res), 1)
