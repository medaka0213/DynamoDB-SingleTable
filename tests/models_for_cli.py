import logging

from ddb_single.model import BaseModel, DBField
from tests.conftest import make_table

logging.basicConfig(level=logging.INFO)

table = make_table("table_cli_test_")
table.init()


class User(BaseModel):
    __table__ = table
    __model_name__ = "user"
    name = DBField(unique_key=True)
    email = DBField(search_key=True)
