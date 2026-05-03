import unittest

from boto3.dynamodb.conditions import Key

from ddb_single import utils_botos as util_b
from ddb_single.error import InvalidParameterError
from ddb_single.key_condition_util import (
    iter_key_attributes_used_in_key_condition,
    validate_single_condition_per_key,
)
from ddb_single.table import SearchExpression, Table, _coerce_search_expression_filter_status


class TestKeyConditionUtil(unittest.TestCase):
    def test_iter_single_partition_and_sort(self):
        kce = Key("sk").eq("search_user_name") & Key("data").eq("x")
        self.assertEqual(
            sorted(iter_key_attributes_used_in_key_condition(kce)), ["data", "sk"]
        )

    def test_iter_detects_duplicate_keys(self):
        kce = Key("sk").eq("a") & Key("data").eq("x") & Key("sk").eq("b")
        names = list(iter_key_attributes_used_in_key_condition(kce))
        self.assertEqual(names.count("sk"), 2)
        self.assertEqual(names.count("data"), 1)

    def test_validate_accepts_valid_gsi_key(self):
        kce = Key("sk").eq("search_rocket_name") & Key("data").eq("falcon")
        validate_single_condition_per_key(kce)

    def test_validate_accepts_lte_gte_boto3_class_names(self):
        kce = Key("sk").eq("search_user_age") & Key("data-n").lte(15)
        validate_single_condition_per_key(kce)
        kce = Key("sk").eq("search_user_age") & Key("data-n").gte(10)
        validate_single_condition_per_key(kce)

    def test_validate_rejects_duplicate_data(self):
        kce = Key("sk").eq("search_model_name") & Key("data").eq("v") & Key("data").eq("w")
        with self.assertRaises(InvalidParameterError) as ctx:
            validate_single_condition_per_key(kce)
        self.assertIn("data", str(ctx.exception))

    def test_iter_rejects_unknown_node_type(self):
        class UnknownCondition:
            pass

        with self.assertRaises(InvalidParameterError):
            list(iter_key_attributes_used_in_key_condition(UnknownCondition()))

    def test_coerce_filter_status_string_staged(self):
        ex = SearchExpression(FilterStatus="staged")
        _coerce_search_expression_filter_status(ex)
        self.assertIs(ex.FilterStatus, util_b.FilterStatus.STAGED)

    def test_coerce_filter_status_enum_unchanged(self):
        ex = SearchExpression(FilterStatus=util_b.FilterStatus.FILTER)
        _coerce_search_expression_filter_status(ex)
        self.assertIs(ex.FilterStatus, util_b.FilterStatus.FILTER)

    def test_search_simple_path_rejects_gsi_shape_on_search_status(self):
        table = Table(
            table_name="t",
            endpoint_url="http://localhost:8000",
            region_name="us-west-2",
            aws_access_key_id="f",
            aws_secret_access_key="f",
        )
        bad = SearchExpression(
            FilterStatus=util_b.FilterStatus.SEARCH,
            KeyConditionExpression=Key("sk").eq("search_user_name")
            & Key("data").eq("v"),
        )
        with self.assertRaises(InvalidParameterError) as ctx:
            table.search("user", bad)
        self.assertIn("primary key", str(ctx.exception).lower())
