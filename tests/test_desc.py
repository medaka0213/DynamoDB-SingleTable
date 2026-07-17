import logging
import unittest

from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from ddb_single.table import FieldType
from tests.conftest import make_table

logging.basicConfig(level=logging.INFO)

table = make_table("desc_test_")
table.init()


class User(BaseModel):
    __table__ = table
    __model_name__ = "user"
    name = DBField(unique_key=True)
    name_ignore_case = DBField(search_key=True, ignore_case=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description = DBField()
    config = DBField(type=FieldType.MAP)


class BlogPost(BaseModel):
    __model_name__ = "blogpost"
    __table__ = table
    title = DBField(unique_key=True)
    content = DBField(search_key=True)
    author = DBField(relation=User)


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
                        "relation_by_unique": True,
                        "ignore_case": False,
                    },
                    "name_ignore_case": {
                        "type": "STRING",
                        "nullable": True,
                        "primary_key": False,
                        "secondary_key": False,
                        "unique_key": False,
                        "search_key": True,
                        "relation": None,
                        "relation_by_unique": True,
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
                        "relation_by_unique": True,
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
                        "relation_by_unique": True,
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
                        "relation_by_unique": True,
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
                        "relation_by_unique": True,
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
                        "relation_by_unique": True,
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
                        "relation_by_unique": True,
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
                        "relation_by_unique": True,
                        "ignore_case": False,
                    },
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
