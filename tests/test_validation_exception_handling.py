import unittest
from unittest.mock import MagicMock

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from ddb_single.table import Table


class TestValidationExceptionHandling(unittest.TestCase):
    def test_query_validation_exception_is_reraised(self):
        table = Table(
            table_name="test_table",
            endpoint_url="http://localhost:8000",
            region_name="us-west-2",
            aws_access_key_id="fakeMyKeyId",
            aws_secret_access_key="fakeSecretAccessKey",
        )
        mock_boto_table = MagicMock()
        error_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "Invalid KeyConditionExpression: KeyConditionExpressions must only contain one condition per key",
            },
            "ResponseMetadata": {"RequestId": "test-request-id"},
        }
        mock_boto_table.query.side_effect = ClientError(error_response, "Query")
        table.__table__ = mock_boto_table

        with self.assertRaises(ClientError) as context:
            table.query(KeyConditionExpression=Key("pk").eq("x"))

        self.assertEqual(
            context.exception.response["Error"]["Code"], "ValidationException"
        )

    def test_query_other_client_errors_return_empty_list(self):
        table = Table(
            table_name="test_table",
            endpoint_url="http://localhost:8000",
            region_name="us-west-2",
            aws_access_key_id="fakeMyKeyId",
            aws_secret_access_key="fakeSecretAccessKey",
        )
        mock_boto_table = MagicMock()
        error_response = {
            "Error": {
                "Code": "ProvisionedThroughputExceededException",
                "Message": "The level of configured provisioned throughput for the table was exceeded",
            },
            "ResponseMetadata": {"RequestId": "test-request-id"},
        }
        mock_boto_table.query.side_effect = ClientError(error_response, "Query")
        table.__table__ = mock_boto_table

        result = table.query(KeyConditionExpression=Key("pk").eq("x"))
        self.assertEqual(result, [])

    def test_scan_validation_exception_is_reraised(self):
        table = Table(
            table_name="test_table",
            endpoint_url="http://localhost:8000",
            region_name="us-west-2",
            aws_access_key_id="fakeMyKeyId",
            aws_secret_access_key="fakeSecretAccessKey",
        )
        mock_boto_table = MagicMock()
        error_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "Invalid scan parameters",
            },
            "ResponseMetadata": {"RequestId": "test-request-id"},
        }
        mock_boto_table.scan.side_effect = ClientError(error_response, "Scan")
        table.__table__ = mock_boto_table

        with self.assertRaises(ClientError) as context:
            table.scan()

        self.assertEqual(
            context.exception.response["Error"]["Code"], "ValidationException"
        )
