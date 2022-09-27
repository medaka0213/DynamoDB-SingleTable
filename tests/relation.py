import unittest
import asyncio

from ddb_single.table import Table
from ddb_single.model import BaseModel, DBField

query = Table(
    table_name="rel_test",
    endpoint_url="http://localhost:8000",
)
query.init_table()

class User(BaseModel):
    __model_name__ = "user"
    __table__ = query
    pk = DBField(primary_key=True)
    sk = DBField(secondary_key=True)
    unique = DBField(unique_key=True)
    name = DBField(search_key=True)
    attr = DBField()


class Message(BaseModel):
    __model_name__ = "user"
    __table__ = query
    pk = DBField(primary_key=True)
    sk = DBField(secondary_key=True)
    unique = DBField(unique_key=True)
    content = DBField()
    user = DBField(reletion=User)


class Sample(unittest.TestCase):
    def test_create(self):
        user = User(unique="test", name="test", attr="test")
        print("user", user.data)
        user.create()

        message = Message(unique="test", content="test", user=user.get_unique())
        print("message", message.data)
        message.create()