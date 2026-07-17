"""
Tests for invalid KeyConditionExpression (duplicate key attributes).

Previously DynamoDB returned ValidationException; ddb_single now rejects these
before the API call (GitHub issue #967).
"""

import logging
import unittest

from boto3.dynamodb.conditions import Key

from ddb_single.error import InvalidParameterError
from tests.conftest import make_table

logging.basicConfig(level=logging.DEBUG)

table = make_table("duplicate_key_test_")


class TestDuplicateKeyCondition(unittest.TestCase):
    """Invalid KeyConditionExpression is rejected before DynamoDB Query."""

    def test_duplicate_range_key_condition(self):
        # sk = search_testModel_name AND data = test1 AND data = test1
        invalid_key_condition = (
            Key("sk").eq("search_testModel_name")
            & Key("data").eq("test1")
            & Key("data").eq("test1")  # Duplicate condition on 'data'
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
            & Key("data").begins_with("test")  # Second condition on 'data'
        )

        with self.assertRaises(InvalidParameterError):
            table.query(
                KeyConditionExpression=invalid_key_condition,
                IndexName="DataSearchIndex",
            )


if __name__ == "__main__":
    unittest.main()
