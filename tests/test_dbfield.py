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

    def test_string_set_field_valid(self):
        field = DBField(type=FieldType.STRING_SET)
        # Each element is converted to str and the result is a set.
        self.assertEqual(field.validate(["a", "b", "a"]), {"a", "b"})
        self.assertEqual(field.validate({"x", "y"}), {"x", "y"})
        self.assertEqual(field.validate([1, 2]), {"1", "2"})

    def test_number_set_field_valid(self):
        field = DBField(type=FieldType.NUMBER_SET)
        # Regression for issue #116: a list of numbers used to be str()-ed and
        # converted character-by-character, so [1, 2] always failed.
        self.assertEqual(field.validate([1, 2]), {Decimal("1"), Decimal("2")})
        self.assertEqual(field.validate([1.5, "2.5"]), {Decimal("1.5"), Decimal("2.5")})
        self.assertEqual(field.validate({3, 4}), {Decimal("3"), Decimal("4")})
        self.assertEqual(field.validate((5,)), {Decimal("5")})

    def test_number_set_field_invalid_element(self):
        field = DBField(type=FieldType.NUMBER_SET)
        with self.assertRaises(ValidationError):
            field.validate([1, "not a number"])

    def test_binary_set_field_valid(self):
        field = DBField(type=FieldType.BINARY_SET)
        # str elements are utf-8 encoded, others go through bytes() like the scalar BINARY type.
        self.assertEqual(field.validate(["abc", b"def"]), {b"abc", b"def"})
        self.assertEqual(field.validate([bytearray(b"xy")]), {b"xy"})

    def test_set_field_rejects_non_collection(self):
        for field_type in (FieldType.STRING_SET, FieldType.NUMBER_SET, FieldType.BINARY_SET):
            field = DBField(type=field_type)
            with self.assertRaises(ValidationError):
                field.validate("not a collection")

    def test_validation_error_message_hides_raw_value(self):
        # 例外メッセージに実データ値 (PII の恐れ) を含めない。型・長さのみ。
        field = DBField(type=FieldType.LIST)
        field.name = "secret_field"
        raw_value = "raw-secret-value"
        with self.assertRaises(ValidationError) as ctx:
            field.validate(raw_value)
        message = str(ctx.exception)
        self.assertNotIn(raw_value, message)
        self.assertIn("secret_field", message)
        self.assertIn("type=str", message)

        field2 = DBField(type=FieldType.STRING)
        field2.name = "secret_field2"
        with self.assertRaises(ValidationError) as ctx:
            field2.validate(["raw-secret-item"])
        message = str(ctx.exception)
        self.assertNotIn("raw-secret-item", message)
        self.assertIn("type=list", message)

    def test_default_value_is_validated(self):
        # A default supplied when no value is given must still be type-validated.
        field = DBField(type=FieldType.NUMBER, default=5)
        self.assertEqual(field.validate(None), Decimal("5"))


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
