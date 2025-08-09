import unittest
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from ddb_single.utils_botos import range_ex, attr_ex, attr_method, is_same_json, json_import, json_export, QueryType
from ddb_single.error import InvalidParameterError


class TestUtilsBotos(unittest.TestCase):

    def test_range_ex(self):
        # Equal mode
        res = range_ex('test', 'value', QueryType.EQ)
        self.assertEqual(res, Key('test').eq('value'))

        # Between mode
        res = range_ex('test', [1, 10], QueryType.BETWEEN)
        self.assertEqual(res, Key('test').between(1, 10))

        # Invalid mode
        with self.assertRaises(InvalidParameterError):
            range_ex('test', 'value', 'INVALID_MODE')

    def test_attr_ex(self):
        # Contains mode
        res = attr_ex('test', 'value', QueryType.CONTAINS)
        self.assertEqual(res, Attr('test').contains('value'))

        # In mode
        res = attr_ex('test', ['value1', 'value2'], QueryType.IN)
        self.assertEqual(res, Attr('test').is_in(['value1', 'value2']))

        # Invalid mode
        with self.assertRaises(InvalidParameterError):
            attr_ex('test', 'value', 'INVALID_MODE')

    def test_attr_method(self):
        # Equal mode
        method = attr_method('test', 'value', QueryType.EQ)
        self.assertTrue(method({'test': 'value'}))
        self.assertFalse(method({'test': 'wrong_value'}))

        # Between mode
        method = attr_method('test', [1, 10], QueryType.BETWEEN)
        self.assertTrue(method({'test': 5}))
        self.assertFalse(method({'test': 11}))

        # Invalid mode
        with self.assertRaises(InvalidParameterError):
            attr_method('test', 'value', 'INVALID_MODE')

    def test_is_same_json(self):
        # Same dictionaries
        data_1 = {'key1': 'value1', 'key2': 'value2'}
        data_2 = {'key1': 'value1', 'key2': 'value2'}
        self.assertTrue(is_same_json(data_1, data_2))

        # Different dictionaries
        data_3 = {'key1': 'value1', 'key2': 'different_value'}
        self.assertFalse(is_same_json(data_1, data_3))

        # None comparison
        self.assertTrue(is_same_json(None, None))
        self.assertFalse(is_same_json(data_1, None))
        self.assertFalse(is_same_json(None, data_1))

        # Different types
        self.assertFalse(is_same_json({'key': 'value'}, ['key', 'value']))

    def test_json_import(self):
        data = {
            'key1': 1.23,
            'key2': [2.34, 3.45],
            'key3': {'key4': 4.56}
        }
        expected = {
            'key1': Decimal('1.23'),
            'key2': [Decimal('2.34'), Decimal('3.45')],
            'key3': {'key4': Decimal('4.56')}
        }
        self.assertEqual(json_import(data), expected)

    def test_json_export(self):
        data = {
            'key1': Decimal('1.23'),
            'key2': [Decimal('2.34'), Decimal('3.45')],
            'key3': {'key4': Decimal('4.56')}
        }
        expected = {
            'key1': 1.23,
            'key2': [2.34, 3.45],
            'key3': {'key4': 4.56}
        }
        self.assertEqual(json_export(data), expected)


if __name__ == '__main__':
    unittest.main()
