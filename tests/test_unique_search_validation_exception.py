"""
Test to reproduce the ValidationException issue with unique key searches.

This test reproduces the issue where searching by unique key causes:
"ValidationException: Invalid KeyConditionExpression:
 KeyConditionExpressions must only contain one condition per key"
"""

import logging
import unittest

from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from ddb_single.table import FieldType
from tests.conftest import make_table

logging.basicConfig(level=logging.DEBUG)

table = make_table("unique_search_test_")
table.init()


class NewsList(BaseModel):
    """Model similar to the real NewsList that causes the issue"""

    __table__ = table
    __model_name__ = "newsList"
    name = DBField(unique_key=True)
    news_list = DBField(type=FieldType.LIST)


query = Query(table)

print("table_name:", table.__table_name__)


class TestUniqueSearchValidationException(unittest.TestCase):
    """Test case to reproduce the ValidationException issue"""

    def setUp(self):
        """Set up test data"""
        # Create a NewsList item with name "youtube-VideoFromSpace"
        news_list_item = NewsList(name="youtube-VideoFromSpace", news_list=["news1", "news2", "news3"])
        query.model(news_list_item).create()

    def test_get_by_unique_should_not_throw_validation_exception(self):
        """
        Test that searching by unique key does not cause ValidationException.

        This reproduces the issue from:
        GET /api-v2/q/newsList/u/youtube-VideoFromSpace/

        Expected: Should return the item or None without exceptions
        Actual (before fix): ClientError with ValidationException is caught
                            and empty list is returned, logged as error
        """
        # This should work without throwing ValidationException
        result = query.model(NewsList).get_by_unique("youtube-VideoFromSpace")

        # Should return the item, not None
        self.assertIsNotNone(result, "get_by_unique should return the item, not None")
        self.assertEqual(result["name"], "youtube-VideoFromSpace")
        self.assertEqual(result["news_list"], ["news1", "news2", "news3"])

    def test_search_by_unique_key_eq(self):
        """
        Test searching by unique key using eq() directly.

        This is what happens internally in get_by_unique().
        """
        # This is what get_by_unique does internally
        result = query.model(NewsList).search(NewsList.name.eq("youtube-VideoFromSpace"))

        # Should return the item in a list
        self.assertEqual(len(result), 1, "search should return exactly one item")
        self.assertEqual(result[0]["name"], "youtube-VideoFromSpace")
        self.assertEqual(result[0]["news_list"], ["news1", "news2", "news3"])

    def test_multiple_unique_searches(self):
        """Test multiple unique key searches to ensure consistency"""
        # Create more items
        query.model(NewsList(name="test-item-1", news_list=["a"])).create()
        query.model(NewsList(name="test-item-2", news_list=["b"])).create()

        # Search for each one
        result1 = query.model(NewsList).get_by_unique("youtube-VideoFromSpace")
        result2 = query.model(NewsList).get_by_unique("test-item-1")
        result3 = query.model(NewsList).get_by_unique("test-item-2")

        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
        self.assertIsNotNone(result3)

        self.assertEqual(result1["name"], "youtube-VideoFromSpace")
        self.assertEqual(result2["name"], "test-item-1")
        self.assertEqual(result3["name"], "test-item-2")


if __name__ == "__main__":
    unittest.main()
