import unittest
import asyncio

from ddb_single.table import FieldType, Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

table = Table(
    table_name="rel_test",
    endpoint_url="http://localhost:8000",
)
table.init()

class User(BaseModel):
    __model_name__ = "user"
    __table__=table
    pk = DBField(primary_key=True)
    sk = DBField(secondary_key=True)
    unique = DBField(unique_key=True)
    name = DBField(search_key=True)
    attr = DBField()


class Message(BaseModel):
    __model_name__ = "message"
    __table__=table
    pk = DBField(primary_key=True)
    sk = DBField(secondary_key=True)
    unique = DBField(unique_key=True)
    content = DBField()
    user = DBField(reletion=User)

query = Query(table)

class Sample(unittest.TestCase):
    def test_create(self):
        user = User(unique="test", name="test", attr="test")
        print("test", user)
        query.model(user).create()

        message = Message(unique="test", content="test", user=user)
        print("message", message)
        query.model(message).create()
