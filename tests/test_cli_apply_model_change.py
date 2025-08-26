import unittest
from boto3.dynamodb.conditions import Key
from click.testing import CliRunner
from ddb_single.table import SearchExpression
import ddb_single.utils_botos as util_b
from ddb_single.query import Query
import ddb_single._cli as cli_mod

from tests.models_for_cli import table, User


class TestApplyModelChangeRecords(unittest.TestCase):
    def setUp(self):
        self.query = Query(table)
        user = User(name="alice", email="alice@example.com")
        q = self.query.model(user)
        search_items, _ = q._search_items()
        q.create()
        table.batch_delete_items(search_items)

    def test_apply_model_change_records(self):
        searchEx = [
            SearchExpression(
                FilterStatus=util_b.FilterStatus.STAGED,
                IndexName=table.__search_index__,
                KeyConditionExpression=Key("sk").eq("search_user_email")
                & Key("data").eq("alice@example.com"),
            )
        ]
        res = table.search("user", *searchEx)
        self.assertEqual(len(res), 0)
        runner = CliRunner()
        result = runner.invoke(cli_mod.cli, ["apply-model-change", "tests.models_for_cli"])
        self.assertEqual(result.exit_code, 0)

        res = table.search("user", *searchEx)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["email"], "alice@example.com")

    def test_apply_model_change_records_invalid_module(self):
        runner = CliRunner()
        result = runner.invoke(cli_mod.cli, ["apply-model-change", "tests.missing_module"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("module not found", result.output)


if __name__ == "__main__":
    unittest.main()
