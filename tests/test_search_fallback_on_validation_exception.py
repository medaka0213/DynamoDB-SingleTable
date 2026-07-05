import unittest
from unittest.mock import patch

from botocore.exceptions import ClientError
from ddb_single.error import InvalidParameterError
from ddb_single.model import BaseModel, DBField
from ddb_single.table import Table
from ddb_single.utils_botos import FilterStatus


def _validation_exception(message: str) -> ClientError:
    return ClientError(
        error_response={
            "Error": {
                "Code": "ValidationException",
                "Message": message,
            }
        },
        operation_name="Query",
    )


def _client_error(code: str, message: str) -> ClientError:
    return ClientError(
        error_response={
            "Error": {
                "Code": code,
                "Message": message,
            }
        },
        operation_name="Query",
    )


class Rocket(BaseModel):
    __table__ = Table(
        table_name="dummy",
        region_name="us-west-2",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )
    __model_name__ = "rocket"
    name = DBField(unique_key=True, ignore_case=True)


class TestSearchFallbackOnValidationException(unittest.TestCase):
    def test_fallback_to_rangeindex_and_inmemory_filter_on_searchindex_validation_exception(self):
        table = Rocket.__table__
        model = Rocket(__skip_validation__=True)
        expr = model.get_field("name").eq("Long March 5B")
        self.assertEqual(expr.FilterStatus, FilterStatus.STAGED)

        calls: list[tuple[str, str | None]] = []

        def fake_query(**kwargs):
            calls.append(("query", kwargs.get("IndexName")))
            # First attempt: SearchIndex query -> DynamoDB rejects it
            if kwargs.get("IndexName") == expr.IndexName:
                # We do not rely on the exact condition tree shape; we only simulate the service behavior.
                raise _validation_exception("KeyConditionExpressions must only contain one condition per key")

            # Fallback: RangeIndex to list candidate PKs
            if kwargs.get("IndexName") == table.__range_index_name__:
                return [
                    {table.__primary_key__: "rocket_1"},
                    {table.__primary_key__: "rocket_2"},
                ]
            raise AssertionError(f"Unexpected query call: {kwargs}")

        def fake_batch_get_from_pks(pks):
            calls.append(("batch_get_from_pks", ",".join(pks)))
            # Candidate items contain mixed-case names; filter should be ignore-case.
            items = {
                "rocket_1": {table.__primary_key__: "rocket_1", "name": "Long March 5B"},
                "rocket_2": {table.__primary_key__: "rocket_2", "name": "Falcon 9"},
            }
            return [items[pk] for pk in pks]

        with (
            patch.object(table, "query", side_effect=fake_query),
            patch.object(table, "batch_get_from_pks", side_effect=fake_batch_get_from_pks),
        ):
            res = table.search(Rocket.__model_name__, expr)
        self.assertEqual([r[table.__primary_key__] for r in res], ["rocket_1"])
        self.assertIn(("query", expr.IndexName), calls)
        self.assertIn(("query", table.__range_index_name__), calls)
        self.assertEqual(
            [call for call in calls if call[0] == "batch_get_from_pks"],
            [
                ("batch_get_from_pks", "rocket_1,rocket_2"),
                ("batch_get_from_pks", "rocket_1"),
            ],
        )

    def test_fallback_to_rangeindex_on_invalid_parameter_error(self):
        table = Rocket.__table__
        model = Rocket(__skip_validation__=True)
        expr = model.get_field("name").eq("Long March 5B")
        calls: list[tuple[str, str | None]] = []

        def fake_query(**kwargs):
            calls.append(("query", kwargs.get("IndexName")))
            if kwargs.get("IndexName") == expr.IndexName:
                raise InvalidParameterError("duplicate key condition")
            if kwargs.get("IndexName") == table.__range_index_name__:
                return [{table.__primary_key__: "rocket_1"}]
            raise AssertionError(f"Unexpected query call: {kwargs}")

        def fake_batch_get_from_pks(pks):
            calls.append(("batch_get_from_pks", ",".join(pks)))
            return [{table.__primary_key__: "rocket_1", "name": "Long March 5B"}]

        with (
            patch.object(table, "query", side_effect=fake_query),
            patch.object(table, "batch_get_from_pks", side_effect=fake_batch_get_from_pks),
        ):
            res = table.search(Rocket.__model_name__, expr)

        self.assertEqual([r[table.__primary_key__] for r in res], ["rocket_1"])
        self.assertIn(("query", expr.IndexName), calls)
        self.assertIn(("query", table.__range_index_name__), calls)

    def test_non_validation_client_error_is_reraised(self):
        table = Rocket.__table__
        model = Rocket(__skip_validation__=True)
        expr = model.get_field("name").eq("Long March 5B")
        calls: list[tuple[str, str | None]] = []

        def fake_query(**kwargs):
            calls.append(("query", kwargs.get("IndexName")))
            raise _client_error("ProvisionedThroughputExceededException", "rate limited")

        with patch.object(table, "query", side_effect=fake_query), self.assertRaises(ClientError) as context:
            table.search(Rocket.__model_name__, expr)

        self.assertEqual(
            context.exception.response["Error"]["Code"],
            "ProvisionedThroughputExceededException",
        )
        self.assertEqual(calls, [("query", expr.IndexName)])

    def test_fallback_returns_empty_without_batch_get_when_rangeindex_has_no_candidates(self):
        table = Rocket.__table__
        model = Rocket(__skip_validation__=True)
        expr = model.get_field("name").eq("Long March 5B")
        calls: list[tuple[str, str | None]] = []

        def fake_query(**kwargs):
            calls.append(("query", kwargs.get("IndexName")))
            if kwargs.get("IndexName") == expr.IndexName:
                raise _validation_exception("KeyConditionExpressions must only contain one condition per key")
            if kwargs.get("IndexName") == table.__range_index_name__:
                return []
            raise AssertionError(f"Unexpected query call: {kwargs}")

        def fake_batch_get_from_pks(pks):
            calls.append(("batch_get_from_pks", ",".join(pks)))
            return []

        with (
            patch.object(table, "query", side_effect=fake_query),
            patch.object(table, "batch_get_from_pks", side_effect=fake_batch_get_from_pks),
        ):
            res = table.search(Rocket.__model_name__, expr)

        self.assertEqual(res, [])
        self.assertEqual(
            calls,
            [
                ("query", expr.IndexName),
                ("query", table.__range_index_name__),
            ],
        )

    def test_fallback_with_none_filter_method_skips_intermediate_inmemory_filter(self):
        table = Rocket.__table__
        model = Rocket(__skip_validation__=True)
        expr = model.get_field("name").eq("Long March 5B")
        expr.FilterMethod = None
        calls: list[tuple[str, str | None]] = []

        def fake_query(**kwargs):
            calls.append(("query", kwargs.get("IndexName")))
            if kwargs.get("IndexName") == expr.IndexName:
                raise _validation_exception("KeyConditionExpressions must only contain one condition per key")
            if kwargs.get("IndexName") == table.__range_index_name__:
                return [
                    {table.__primary_key__: "rocket_1"},
                    {table.__primary_key__: "rocket_2"},
                ]
            raise AssertionError(f"Unexpected query call: {kwargs}")

        def fake_batch_get_from_pks(pks):
            calls.append(("batch_get_from_pks", ",".join(pks)))
            items = {
                "rocket_1": {table.__primary_key__: "rocket_1", "name": "Long March 5B"},
                "rocket_2": {table.__primary_key__: "rocket_2", "name": "Falcon 9"},
            }
            return [items[pk] for pk in pks]

        with (
            patch.object(table, "query", side_effect=fake_query),
            patch.object(table, "batch_get_from_pks", side_effect=fake_batch_get_from_pks),
        ):
            res = table.search(Rocket.__model_name__, expr)

        self.assertCountEqual([r[table.__primary_key__] for r in res], ["rocket_1", "rocket_2"])
        batch_calls = [call for call in calls if call[0] == "batch_get_from_pks"]
        self.assertEqual(len(batch_calls), 1)
        self.assertEqual(set(batch_calls[0][1].split(",")), {"rocket_1", "rocket_2"})


if __name__ == "__main__":
    unittest.main()
