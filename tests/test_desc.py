import unittest
from ddb_single.table import FieldType, Table
from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query

import datetime
import logging

logging.basicConfig(level=logging.INFO)

table = Table(
    table_name="desc_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
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
    name_ignore_nase = DBField(search_key=True, ignore_case=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description = DBField()
    config = DBField(type=FieldType.MAP)


class BlogPost(BaseModel):
    __model_name__ = "blogpost"
    __table__ = table
    title = DBField(unique_key=True)
    content = DBField(search_key=True)
    author = DBField(reletion=User)


query = Query(table)

print("table_name:", table.__table_name__)


class TestCRUD(unittest.TestCase):
    def test_describe(self):
        res = User.describe()
        self.assertEqual(
            res,
            {
                "model_name": "user",
                "table_name": User.__table__.__table_name__,
                "fields": {
                    "name": {
                        "type": "STRING",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": True,
                        "search_key": True,
                        "relation": None,
                        "reletion_by_unique": True,
                        "ignore_case": False,
                    },
                    "name_ignore_nase": {
                        "type": "STRING",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": False,
                        "search_key": True,
                        "relation": None,
                        "reletion_by_unique": True,
                        "ignore_case": True,
                    },
                    "email": {
                        "type": "STRING",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": False,
                        "search_key": True,
                        "relation": None,
                        "reletion_by_unique": True,
                        "ignore_case": False,
                    },
                    "age": {
                        "type": "NUMBER",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": False,
                        "search_key": True,
                        "relation": None,
                        "reletion_by_unique": True,
                        "ignore_case": False,
                    },
                    "description": {
                        "type": "STRING",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": False,
                        "search_key": False,
                        "relation": None,
                        "reletion_by_unique": True,
                        "ignore_case": False,
                    },
                    "config": {
                        "type": "MAP",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": False,
                        "search_key": False,
                        "relation": None,
                        "reletion_by_unique": True,
                        "ignore_case": False,
                    },
                },
            },
        )

    def test_describe_relation(self):
        res = BlogPost.describe()
        self.assertEqual(
            res,
            {
                "model_name": "blogpost",
                "table_name": BlogPost.__table__.__table_name__,
                "fields": {
                    "title": {
                        "type": "STRING",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": True,
                        "search_key": True,
                        "relation": None,
                        "reletion_by_unique": True,
                        "ignore_case": False,
                    },
                    "content": {
                        "type": "STRING",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": False,
                        "search_key": True,
                        "relation": None,
                        "reletion_by_unique": True,
                        "ignore_case": False,
                    },
                    "author": {
                        "type": "STRING",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": False,
                        "search_key": False,
                        "relation": "user",
                        "reletion_by_unique": True,
                        "ignore_case": False,
                    },
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
