import unittest
import warnings
from decimal import Decimal

from ddb_single.error import ValidationError
from ddb_single.model import DBField
from ddb_single.table import FieldType


class DummyRelation:
    __model_name__ = "DummyModel"
    data = {"dummy": "value"}
    __unique_keys__ = ["dummy"]
    __primary_key__ = "dummy"


class TestDBFieldValidation(unittest.TestCase):
    def test_string_field_valid(self):
        field = DBField(type=FieldType.STRING, nullable=False)
        # Valid string input: returns the string as is.
        result = field.validate("test")
        self.assertEqual(result, "test")

    def test_string_field_invalid(self):
        field = DBField(type=FieldType.STRING, nullable=False)
        # None is not allowed for a non-nullable field.
        with self.assertRaises(ValidationError):
            field.validate(None)
        with self.assertRaises(ValidationError):
            field.validate([])

    def test_number_field_valid(self):
        field = DBField(type=FieldType.NUMBER)
        # Valid number input should be converted to Decimal.
        result = field.validate("123.45")
        self.assertEqual(result, Decimal("123.45"))

    def test_binary_field_valid(self):
        field = DBField(type=FieldType.BINARY)
        # Valid binary input should be converted to bytes.
        result = field.validate("abc")
        self.assertEqual(result, b"abc")

    def test_boolean_field_valid(self):
        field = DBField(type=FieldType.BOOLEAN)
        # Boolean conversion: non-empty string yields True.
        result = field.validate("True")
        self.assertEqual(result, True)

    def test_list_field_valid(self):
        field = DBField(type=FieldType.LIST)
        # For a LIST field, valid input is a list.
        self.assertEqual(field.validate([1, 2, 3]), [1, 2, 3])
        self.assertEqual(field.validate(["a", "b", "c"]), ["a", "b", "c"])
        self.assertEqual(field.validate([]), [])

    def test_list_field_invalid(self):
        field = DBField(type=FieldType.LIST)
        # Non-list input should raise a ValidationError.
        with self.assertRaises(ValidationError):
            field.validate("not a list")

    def test_non_list_field_with_list_input(self):
        field = DBField(type=FieldType.STRING)
        # A field that is not a list should not accept a list input.
        with self.assertRaises(ValidationError):
            field.validate(["not", "a", "string"])


class TestDBFieldRelationBackwardCompat(unittest.TestCase):
    """The misspelled ``reletion`` kwargs are deprecated but still accepted."""

    def test_reletion_alias_maps_to_relation(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            field = DBField(reletion=DummyRelation)
        self.assertIs(field.relation, DummyRelation)
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))

    def test_reletion_by_unique_alias_maps_to_relation_by_unique(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            field = DBField(relation=DummyRelation, reletion_by_unique=False)
        self.assertFalse(field.relation_by_unique)
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))

    def test_relation_takes_precedence_over_reletion(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            field = DBField(relation=DummyRelation, reletion=None)
        self.assertIs(field.relation, DummyRelation)

    def test_new_relation_kwarg_no_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            field = DBField(relation=DummyRelation, relation_by_unique=True)
        self.assertIs(field.relation, DummyRelation)
        self.assertTrue(field.relation_by_unique)
        self.assertFalse(any(issubclass(w.category, DeprecationWarning) for w in caught))


if __name__ == "__main__":
    unittest.main()
