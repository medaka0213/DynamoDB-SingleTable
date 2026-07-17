"""Regression tests for issue #116.

NUMBER_SET / BINARY_SET validation used to call ``str()`` on the input list and
convert it character-by-character (e.g. ``Decimal("[")``), making those field
types unusable. These tests verify that set-type fields validate element-wise
and round-trip through DynamoDB Local.
"""

import datetime
import logging
import unittest
from decimal import Decimal

from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from ddb_single.table import FieldType, Table

logging.basicConfig(level=logging.INFO)

table = Table(
    table_name="set_types_test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    endpoint_url="http://localhost:8000",
    region_name="us-west-2",
    aws_access_key_id="fakeMyKeyId",
    aws_secret_access_key="fakeSecretAccessKey",
)
table.init()


class Item(BaseModel):
    __table__ = table
    __model_name__ = "set_item"
    name = DBField(unique_key=True, nullable=False)
    tags = DBField(type=FieldType.STRING_SET)
    scores = DBField(type=FieldType.NUMBER_SET)
    blobs = DBField(type=FieldType.BINARY_SET)


query = Query(table)


class TestSetTypeRoundTrip(unittest.TestCase):
    def test_set_fields_round_trip(self):
        item = Item(
            name="set_test",
            tags=["red", "blue", "red"],
            scores=[1, 2],  # the exact input that used to break NUMBER_SET
            blobs=["abc", b"def"],
        )
        # Validation happens at model construction: element-wise conversion.
        self.assertEqual(item.data["tags"], {"red", "blue"})
        self.assertEqual(item.data["scores"], {Decimal("1"), Decimal("2")})
        self.assertEqual(item.data["blobs"], {b"abc", b"def"})

        query.model(item).create()
        res = query.model(Item).get(item.data["pk"])
        self.assertIsNotNone(res)
        self.assertEqual(set(res["tags"]), {"red", "blue"})
        self.assertEqual({Decimal(v) for v in res["scores"]}, {Decimal("1"), Decimal("2")})
        self.assertEqual({bytes(v) for v in res["blobs"]}, {b"abc", b"def"})

    def test_set_input_accepted(self):
        item = Item(
            name="set_input_test",
            tags={"a", "b"},
            scores={Decimal("3"), Decimal("4.5")},
        )
        self.assertEqual(item.data["tags"], {"a", "b"})
        self.assertEqual(item.data["scores"], {Decimal("3"), Decimal("4.5")})

        query.model(item).create()
        res = query.model(Item).get(item.data["pk"])
        self.assertIsNotNone(res)
        self.assertEqual(set(res["tags"]), {"a", "b"})
        self.assertEqual({Decimal(v) for v in res["scores"]}, {Decimal("3"), Decimal("4.5")})


if __name__ == "__main__":
    unittest.main()
