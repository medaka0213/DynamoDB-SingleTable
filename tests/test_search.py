import logging
import unittest

from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from ddb_single.table import FieldType
from tests.conftest import make_table

logging.basicConfig(level=logging.INFO)

table = make_table("search_test_")
table.init()


class User(BaseModel):
    __table__ = table
    __model_name__ = "user"
    name = DBField(unique_key=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description = DBField()


class UserNotFound(BaseModel):
    __table__ = table
    __model_name__ = "userNotFound"
    name = DBField(unique_key=True)


query = Query(table)

print("table_name:", table.__table_name__)


class TestSearch(unittest.TestCase):
    def setUp(self):
        test = User(name="test1", age=21)
        query.model(test).create()
        test = User(name="test2", age=22)
        query.model(test).create()
        test = User(name="test3", age=23)
        query.model(test).create()
        test = User(name="123", age=24)  # 数字の名前
        query.model(test).create()
        test = UserNotFound(name="testNotFound")
        query.model(test).create()

    def test_search(self):
        res = query.model(User).search(User.name.eq("test1"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test1")

    def test_search_num_as_str(self):
        res = query.model(User).search(User.name.eq(123))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "123")

    def test_search_str_as_num(self):
        res = query.model(User).search(User.age.eq("22"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["age"], 22)

    def test_get_by_unique(self):
        res = query.model(User).get_by_unique("test2")
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "test2")

    def test_search_by_get_field(self):
        res = query.model(User).search(User().get_field("name").eq("test3"))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "test3")

    def test_get_all(self):
        res = query.model(User).search()
        self.assertEqual(len(res), 4)
        self.assertIsInstance(res[0], dict)

    def test_not_equal(self):
        res = query.model(User).search(User.name.ne("test1"))
        self.assertEqual(len(res), 3)
        self.assertIsInstance(res[0], dict)

    def test_begins(self):
        res = query.model(User).search(User.name.begins_with("test"))
        self.assertEqual(len(res), 3)
        self.assertIsInstance(res[0], dict)

    def test_between(self):
        res = query.model(User).search(User.name.between("test1", "test2"))
        self.assertEqual(len(res), 2)
        self.assertIn(res[0]["name"], ["test1", "test2"])
        self.assertIn(res[1]["name"], ["test1", "test2"])

    def test_between_num_as_str(self):
        res = query.model(User).search(User.name.between(100, 200))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "123")

    def test_between_str_as_num(self):
        res = query.model(User).search(User.age.between("22", "24"))
        self.assertEqual(len(res), 3)
        self.assertIn(res[0]["age"], [22, 23, 24])
        self.assertIn(res[1]["age"], [22, 23, 24])

    def test_limit(self):
        res = query.model(User).search(limit=1)
        self.assertEqual(len(res), 1)
        self.assertIn(res[0]["name"], ["test1", "test2", "test3", "123"])

    def test_pk_only(self):
        res = query.model(User).search(User().get_field("name").eq("test3"), pk_only=True)
        self.assertEqual(len(res), 1)
        self.assertIsInstance(res[0], str)

    def test_pk_only_not_staged(self):
        res = query.model(User).search(pk_only=True)
        self.assertEqual(len(res), 4)
        self.assertIsInstance(res[0], str)

    def test_empty(self):
        with self.assertNoLogs(logger=logging.getLogger("ddb_single.table"), level=logging.ERROR):
            res = query.model(User).search(User.name.eq(""))
            self.assertEqual(len(res), 0)

    def test_combined_begins_and_not_equal(self):
        """Test combining BEGINS and N_EQ filters (AND condition)"""
        res = query.model(User).search(User.name.begins_with("test"), User.name.ne("test1"))
        self.assertEqual(len(res), 2)
        names = [r["name"] for r in res]
        self.assertIn("test2", names)
        self.assertIn("test3", names)
        self.assertNotIn("test1", names)

    def test_combined_filters_with_description(self):
        """Test combining search_key field and non-search_key field filters"""
        test1 = User(name="special1", age=30, description="Special item - apple")
        query.model(test1).create()
        test2 = User(name="special2", age=31, description="Special item - banana")
        query.model(test2).create()

        try:
            res = query.model(User).search(
                User.name.begins_with("special"), User.description.ne("Special item - apple")
            )
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["name"], "special2")
            self.assertEqual(res[0]["description"], "Special item - banana")
        finally:
            # Clean up created items to avoid affecting other tests
            query.model(test1).delete()
            query.model(test2).delete()

    def test_staged_combined_with_primary_key(self):
        """A staged (search_key) condition combined with a primary-key (SEARCH)
        condition must intersect both: the pk condition has to narrow the staged
        candidate set, not be dropped."""
        userA = User(name="staged_pk_A", age=77)
        query.model(userA).create()
        userB = User(name="staged_pk_B", age=77)
        query.model(userB).create()
        pk_a = userA.data[table.__primary_key__]
        pk_field = User(__skip_validation__=True).get_field(table.__primary_key__)

        try:
            # age.eq(77) is STAGED (both users match); pk_field.eq(pk_a) is a
            # SEARCH condition that must restrict the result to userA only.
            res = query.model(User).search(User.age.eq(77), pk_field.eq(pk_a))
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["name"], "staged_pk_A")
            self.assertEqual(res[0][table.__primary_key__], pk_a)
        finally:
            query.model(userA).delete()
            query.model(userB).delete()


if __name__ == "__main__":
    unittest.main()
