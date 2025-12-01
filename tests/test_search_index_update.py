import datetime
import unittest

from boto3.dynamodb.conditions import Key

from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from ddb_single.table import Table


table = Table(
    table_name="search_update_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    endpoint_url="http://localhost:8000",
    region_name="us-west-2",
    aws_access_key_id="fakeMyKeyId",
    aws_secret_access_key="fakeSecretAccessKey",
)
table.init()


class SearchableModel(BaseModel):
    __table__ = table
    __model_name__ = "searchable_model"
    name = DBField(unique_key=True)
    search_key = DBField(search_key=True)


query = Query(table)


class TestSearchIndexUpdate(unittest.TestCase):
    def test_search_index_survives_update(self):
        original = SearchableModel(name="user1", search_key="2024-01-01T00:00:00Z")
        query.model(original).create()

        res_before = query.model(SearchableModel).search(
            SearchableModel.search_key.eq("2024-01-01T00:00:00Z")
        )
        self.assertEqual(len(res_before), 1)

        updated = SearchableModel(name="user1", search_key="2024-02-01T00:00:00Z")
        query.model(updated).update()

        res_after = query.model(SearchableModel).search(
            SearchableModel.search_key.eq("2024-02-01T00:00:00Z")
        )
        self.assertEqual(len(res_after), 1)
        self.assertEqual(res_after[0]["search_key"], "2024-02-01T00:00:00Z")

        old_res = query.model(SearchableModel).search(
            SearchableModel.search_key.eq("2024-01-01T00:00:00Z")
        )
        self.assertEqual(len(old_res), 0)

    def test_search_index_recreated_when_missing_before_update(self):
        original = SearchableModel(name="user1", search_key="2024-01-01T00:00:00Z")
        query.model(original).create()

        pk_value = original.data[original.__primary_key__]
        search_sk_prefix = table.search_key_factory(
            SearchableModel.__model_name__, "search_key"
        )
        search_items = table.query(
            KeyConditionExpression=(
                Key(table.__primary_key__).eq(pk_value)
                & Key(table.__secondary_key__).begins_with(search_sk_prefix)
            )
        )
        table.batch_delete_items(search_items)

        res_missing = query.model(SearchableModel).search(
            SearchableModel.search_key.eq("2024-01-01T00:00:00Z")
        )
        self.assertEqual(len(res_missing), 0)

        updated = SearchableModel(name="user1", search_key="2024-02-01T00:00:00Z")
        query.model(updated).update()

        res_after = query.model(SearchableModel).search(
            SearchableModel.search_key.eq("2024-02-01T00:00:00Z")
        )
        self.assertEqual(len(res_after), 1)
        self.assertEqual(res_after[0]["search_key"], "2024-02-01T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
