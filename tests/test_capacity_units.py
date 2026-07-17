import unittest

from tests.conftest import make_table


class TestCapacityUnits(unittest.TestCase):
    def test_create_table_uses_write_capacity_for_writes(self):
        """create_table() must apply WriteCapacityUnits to the write throughput,
        not the read setting."""
        table = make_table("capacity_test_", ReadCapacityUnits=3, WriteCapacityUnits=7)
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
