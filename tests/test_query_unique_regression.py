import datetime
import unittest

from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from ddb_single.table import Table


table = Table(
    table_name="query_unique_regression_"
    + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    endpoint_url="http://localhost:8000",
    region_name="us-west-2",
    aws_access_key_id="fakeMyKeyId",
    aws_secret_access_key="fakeSecretAccessKey",
)
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
