import datetime
import unittest

from boto3.dynamodb.conditions import Key

from ddb_single.error import InvalidParameterError
from ddb_single.table import Table


table = Table(
    table_name="duplicate_key_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    endpoint_url="http://localhost:8000",
    region_name="us-west-2",
    aws_access_key_id="fakeMyKeyId",
    aws_secret_access_key="fakeSecretAccessKey",
)


class TestDuplicateKeyCondition(unittest.TestCase):
    def test_duplicate_range_key_condition(self):
        invalid_key_condition = (
            Key("sk").eq("search_testModel_name")
            & Key("data").eq("test1")
            & Key("data").eq("test1")
        )

        with self.assertRaises(InvalidParameterError) as context:
            table.query(
                KeyConditionExpression=invalid_key_condition,
                IndexName="DataSearchIndex",
            )

        self.assertIn("multiple conditions", str(context.exception).lower())
        self.assertIn("data", str(context.exception).lower())

    def test_multiple_different_conditions_same_key(self):
        invalid_key_condition = (
            Key("sk").eq("search_testModel_name")
            & Key("data").eq("test1")
            & Key("data").begins_with("test")
        )

        with self.assertRaises(InvalidParameterError):
            table.query(
                KeyConditionExpression=invalid_key_condition,
                IndexName="DataSearchIndex",
            )
