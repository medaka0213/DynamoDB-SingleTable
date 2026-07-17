"""
Test that ValidationException is properly re-raised instead of being silently caught.
"""

import logging
import time
import unittest
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from ddb_single.table import Table

logging.basicConfig(level=logging.INFO)


def _make_table() -> Table:
    """Build a Table with a unique name (never connects to DynamoDB in these tests)."""
    return Table(
        table_name=f"test_{time.time_ns()}",
        endpoint_url="http://localhost:8000",
        region_name="us-west-2",
        aws_access_key_id="fakeMyKeyId",
        aws_secret_access_key="fakeSecretAccessKey",
    )


class TestValidationExceptionHandling(unittest.TestCase):
    """Test that ValidationException is properly handled"""

    def test_query_validation_exception_is_reraised(self):
        """
        Test that when a ValidationException occurs in query(),
        it is re-raised instead of being caught and returning empty list.
        """
        # Create a table without actually connecting to DynamoDB
        table = _make_table()

        # Create a mock table
        mock_boto_table = MagicMock()

        # Create a mock ValidationException response
        error_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "Invalid KeyConditionExpression: KeyConditionExpressions must only contain one condition per key",
            },
            "ResponseMetadata": {"RequestId": "test-request-id"},
        }
        mock_boto_table.query.side_effect = ClientError(error_response, "Query")

        # Set the mock table directly (bypassing init())
        table.__table__ = mock_boto_table

        # The ValidationException should be re-raised, not caught
        with self.assertRaises(ClientError) as context:
            table.query()

        # Verify it's a ValidationException
        self.assertEqual(context.exception.response["Error"]["Code"], "ValidationException")

    def _table_with_error(self, operation, error_code, error_message, fail_on_second_page=False):
        """Build a Table whose boto3 table raises the given ClientError.

        With ``fail_on_second_page=True``, the first call returns a page with a
        ``LastEvaluatedKey`` and the error is raised on the pagination call.
        """
        table = _make_table()
        mock_boto_table = MagicMock()
        error_response = {
            "Error": {"Code": error_code, "Message": error_message},
            "ResponseMetadata": {"RequestId": "test-request-id"},
        }
        error = ClientError(error_response, operation)
        if fail_on_second_page:
            first_page = {
                "Items": [{"pk": "test_item_1", "sk": "test_item"}],
                "LastEvaluatedKey": {"pk": "test_item_1", "sk": "test_item"},
            }
            side_effect = [first_page, error]
        else:
            side_effect = error
        getattr(mock_boto_table, operation.lower()).side_effect = side_effect
        # Set the mock table directly (bypassing init())
        table.__table__ = mock_boto_table
        return table

    def test_query_other_client_errors_are_reraised(self):
        """
        Test that other ClientErrors (not ValidationException) propagate
        instead of being converted into an empty result (fail-open).
        """
        table = self._table_with_error(
            "Query",
            "ProvisionedThroughputExceededException",
            "The level of configured provisioned throughput for the table was exceeded",
        )

        with self.assertRaises(ClientError) as context:
            table.query()

        self.assertEqual(
            context.exception.response["Error"]["Code"],
            "ProvisionedThroughputExceededException",
        )

    def test_query_access_denied_is_reraised(self):
        """AccessDeniedException in query() must propagate, not become an empty result."""
        table = self._table_with_error(
            "Query",
            "AccessDeniedException",
            "User is not authorized to perform: dynamodb:Query",
        )

        with self.assertRaises(ClientError) as context:
            table.query()

        self.assertEqual(context.exception.response["Error"]["Code"], "AccessDeniedException")

    def test_scan_other_client_errors_are_reraised(self):
        """ResourceNotFoundException in scan() must propagate, not become an empty result."""
        table = self._table_with_error(
            "Scan",
            "ResourceNotFoundException",
            "Requested resource not found",
        )

        with self.assertRaises(ClientError) as context:
            table.scan()

        self.assertEqual(context.exception.response["Error"]["Code"], "ResourceNotFoundException")

    def test_query_client_error_during_pagination_is_reraised(self):
        """A ClientError raised while fetching the second page of query() must propagate."""
        table = self._table_with_error(
            "Query",
            "ProvisionedThroughputExceededException",
            "The level of configured provisioned throughput for the table was exceeded",
            fail_on_second_page=True,
        )

        with self.assertRaises(ClientError) as context:
            table.query()

        self.assertEqual(
            context.exception.response["Error"]["Code"],
            "ProvisionedThroughputExceededException",
        )
        # Both the first page and the failing pagination call must have been made
        self.assertEqual(table.__table__.query.call_count, 2)

    def test_scan_client_error_during_pagination_is_reraised(self):
        """A ClientError raised while fetching the second page of scan() must propagate."""
        table = self._table_with_error(
            "Scan",
            "ResourceNotFoundException",
            "Requested resource not found",
            fail_on_second_page=True,
        )

        with self.assertRaises(ClientError) as context:
            table.scan()

        self.assertEqual(context.exception.response["Error"]["Code"], "ResourceNotFoundException")
        # Both the first page and the failing pagination call must have been made
        self.assertEqual(table.__table__.scan.call_count, 2)

    def test_scan_validation_exception_is_reraised(self):
        """
        Test that ValidationException in scan() is also re-raised.
        """
        # Create a table without actually connecting to DynamoDB
        table = _make_table()

        # Create a mock table
        mock_boto_table = MagicMock()

        error_response = {
            "Error": {"Code": "ValidationException", "Message": "Invalid scan parameters"},
            "ResponseMetadata": {"RequestId": "test-request-id"},
        }
        mock_boto_table.scan.side_effect = ClientError(error_response, "Scan")

        # Set the mock table directly (bypassing init())
        table.__table__ = mock_boto_table

        # The ValidationException should be re-raised
        with self.assertRaises(ClientError) as context:
            table.scan()

        # Verify it's a ValidationException
        self.assertEqual(context.exception.response["Error"]["Code"], "ValidationException")


if __name__ == "__main__":
    unittest.main()
