import datetime
import unittest
from boto3.dynamodb.conditions import Key

from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from ddb_single.table import FieldType, Table


class LongText(BaseModel):
    __table__ = None  # placeholder, set in setUp
    __model_name__ = "longtext"
    slug = DBField(unique_key=True, search_key=True)
    body = DBField()


class TestSearchKeyChunking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        table = Table(
            table_name="chunk_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            endpoint_url="http://localhost:8000",
            region_name="us-west-2",
            aws_access_key_id="fakeMyKeyId",
            aws_secret_access_key="fakeSecretAccessKey",
        )
        table.init()
        LongText.__table__ = table
        cls.table = table
        cls.query = Query(table)

    def test_long_search_key_is_chunked_and_searchable(self):
        long_value = "a" * 2500
        article = LongText(slug=long_value, body="sample")
        self.query.model(article).create()

        stored = self.query.model(LongText).get_by_unique(long_value)
        self.assertIsNotNone(stored)

        pk = stored[self.table.__primary_key__]
        data_key = self.table.search_data_key(FieldType.STRING)
        base_sk = self.table.search_key_factory(LongText.__model_name__, "slug")

        items = self.table.query(KeyConditionExpression=Key(self.table.__primary_key__).eq(pk))
        base_items = [i for i in items if i[self.table.__secondary_key__] == base_sk]
        self.assertEqual(len(base_items), 1)
        self.assertEqual(len(base_items[0][data_key]), 64)

        chunk_items = [
            i
            for i in items
            if i[self.table.__secondary_key__].startswith(f"{base_sk}#chunk#")
        ]
        self.assertGreater(len(chunk_items), 1)

        chunk_items = sorted(chunk_items, key=lambda i: i.get("chunk_index", 0))
        reconstructed = "".join(i[data_key] for i in chunk_items)
        self.assertEqual(reconstructed, long_value)

        result = self.query.model(LongText).search(LongText.slug.eq(long_value))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["slug"], long_value)


if __name__ == "__main__":
    unittest.main()
