import unittest

from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from tests.conftest import make_table

table = make_table("query_unique_regression_")
table.init()


class Account(BaseModel):
    __table__ = table
    __model_name__ = "user_account"
    username = DBField(unique_key=True, ignore_case=True)
    email = DBField()


test_query = Query(table)


class TestUniqueSearchRegression(unittest.TestCase):
    def setUp(self):
        record = Account(username="Alice", email="alice@example.com")
        test_query.model(record).create()

    def test_get_by_unique_on_underscored_model(self):
        res = test_query.model(Account).get_by_unique("alice")
        self.assertIsNotNone(res)
        self.assertEqual(res["username"], "Alice")

    def test_get_by_unique_with_multiple_records(self):
        another = Account(username="Bob", email="bob@example.com")
        test_query.model(another).create()

        res = test_query.model(Account).get_by_unique("bob")

        self.assertIsNotNone(res)
        self.assertEqual(res["username"], "Bob")
        self.assertEqual(res["email"], "bob@example.com")


if __name__ == "__main__":
    unittest.main()
