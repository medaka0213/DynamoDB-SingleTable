import datetime
import unittest

from ddb_single.table import Table


class TestCapacityUnits(unittest.TestCase):
    def test_create_table_uses_write_capacity_for_writes(self):
        """create_table() must apply WriteCapacityUnits to the write throughput,
        not the read setting."""
        table = Table(
            table_name="capacity_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"),
            endpoint_url="http://localhost:8000",
            region_name="us-west-2",
            aws_access_key_id="fakeMyKeyId",
            aws_secret_access_key="fakeSecretAccessKey",
            ReadCapacityUnits=3,
            WriteCapacityUnits=7,
        )
        table.init()
        try:
            desc = table.__client__.describe_table(TableName=table.__table_name__)["Table"]
            throughput = desc["ProvisionedThroughput"]
            self.assertEqual(throughput["ReadCapacityUnits"], 3)
            self.assertEqual(throughput["WriteCapacityUnits"], 7)
        finally:
            table.__client__.delete_table(TableName=table.__table_name__)


if __name__ == "__main__":
    unittest.main()
