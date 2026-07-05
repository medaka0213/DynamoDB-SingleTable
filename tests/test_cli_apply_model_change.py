import unittest

from boto3.dynamodb.conditions import Key
from click.testing import CliRunner

import ddb_single._cli as cli_mod
import ddb_single.utils_botos as util_b
from ddb_single.query import Query
from ddb_single.table import SearchExpression
from tests.models_for_cli import User, table  # noqa: I001


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
                KeyConditionExpression=Key("sk").eq("search_user_email") & Key("data").eq("alice@example.com"),
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


class TestModulePathValidation(unittest.TestCase):
    """importlib.import_module へ渡すモジュールパスの検証 (#399)。DB 接続不要"""

    def test_apply_model_change_records_rejects_unsafe_module_path(self):
        """モジュールパス以外の文字列は import 前に拒否される (#399)"""
        unsafe_paths = [
            "../evil",
            "tests/models_for_cli",
            "tests.models_for_cli;import os",
            "tests.models_for_cli os.system('id')",
            "tests..models_for_cli",
            ".tests.models_for_cli",
            "tests.models_for_cli.",
            "123invalid",
            "",
            " ",
        ]
        runner = CliRunner()
        for path in unsafe_paths:
            with self.subTest(path=path):
                result = runner.invoke(cli_mod.cli, ["apply-model-change", path])
                self.assertNotEqual(result.exit_code, 0)
                self.assertIn("invalid module path", result.output)

    def test_module_path_pattern_allows_valid_paths(self):
        """正当なモジュールパスはパターンを通過する (#399)"""
        for path in ["tests.models_for_cli", "a", "a.b.c", "_private.module", "mod_1.sub_2"]:
            with self.subTest(path=path):
                self.assertIsNotNone(cli_mod._MODULE_PATH_PATTERN.fullmatch(path))


if __name__ == "__main__":
    unittest.main()
