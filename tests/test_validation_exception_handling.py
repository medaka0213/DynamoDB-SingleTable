"""
Test that ValidationException is properly re-raised instead of being silently caught.
"""

import logging
import unittest
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from ddb_single.table import Table

logging.basicConfig(level=logging.INFO)


class TestValidationExceptionHandling(unittest.TestCase):
    """Test that ValidationException is properly handled"""

    def test_query_validation_exception_is_reraised(self):
        """
        Test that when a ValidationException occurs in query(),
        it is re-raised instead of being caught and returning empty list.
        """
        # Create a table without actually connecting to DynamoDB
        table = Table(
            table_name="test_table",
            endpoint_url="http://localhost:8000",
            region_name="us-west-2",
            aws_access_key_id="fakeMyKeyId",
            aws_secret_access_key="fakeSecretAccessKey",
        )

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

    def test_query_other_client_errors_return_empty_list(self):
        """
        Test that other ClientErrors (not ValidationException)
        still return empty list as before.
        """
        # Create a table without actually connecting to DynamoDB
        table = Table(
            table_name="test_table",
            endpoint_url="http://localhost:8000",
            region_name="us-west-2",
            aws_access_key_id="fakeMyKeyId",
            aws_secret_access_key="fakeSecretAccessKey",
        )

        # Create a mock table
        mock_boto_table = MagicMock()

        # Create a mock ProvisionedThroughputExceededException
        error_response = {
            "Error": {
                "Code": "ProvisionedThroughputExceededException",
                "Message": "The level of configured provisioned throughput for the table was exceeded",
            },
            "ResponseMetadata": {"RequestId": "test-request-id"},
        }
        mock_boto_table.query.side_effect = ClientError(error_response, "Query")

        # Set the mock table directly (bypassing init())
        table.__table__ = mock_boto_table

        # Other errors should still return empty list
        result = table.query()
        self.assertEqual(result, [])

    def test_scan_validation_exception_is_reraised(self):
        """
        Test that ValidationException in scan() is also re-raised.
        """
        # Create a table without actually connecting to DynamoDB
        table = Table(
            table_name="test_table",
            endpoint_url="http://localhost:8000",
            region_name="us-west-2",
            aws_access_key_id="fakeMyKeyId",
            aws_secret_access_key="fakeSecretAccessKey",
        )

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
