import unittest
from unittest.mock import patch
from decimal import Decimal
from ddb_single.utils_botos import range_ex, attr_ex, attr_method, is_same_json, json_import, json_export, QueryType
from ddb_single.error import InvalidParameterError


class TestUtilsBotos(unittest.TestCase):

    @patch('ddb_single.utils_botos.Key')
    def test_range_ex(self, mock_key):
        # Equal mode
        range_ex('test', 'value', QueryType.EQ)
        mock_key.assert_called_with('test')
        mock_key.return_value.eq.assert_called_with('value')

        # Between mode
        range_ex('test', [1, 10], QueryType.BETWEEN)
        mock_key.return_value.between.assert_called_with(1, 10)

        # Invalid mode
        with self.assertRaises(InvalidParameterError):
            range_ex('test', 'value', 'INVALID_MODE')

    @patch('ddb_single.utils_botos.Attr')
    def test_attr_ex(self, mock_attr):
        # Contains mode
        attr_ex('test', 'value', QueryType.CONTAINS)
        mock_attr.assert_called_with('test')
        mock_attr.return_value.contains.assert_called_with('value')

        # In mode
        attr_ex('test', ['value1', 'value2'], QueryType.IN)
        mock_attr.return_value.in_.assert_called_with(['value1', 'value2'])

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

    def test_is_same_json(self):
        # Same dictionaries
        data_1 = {'key1': 'value1', 'key2': 'value2'}
        data_2 = {'key1': 'value1', 'key2': 'value2'}
        self.assertTrue(is_same_json(data_1, data_2))

        # Different dictionaries
        data_3 = {'key1': 'value1', 'key2': 'different_value'}
        self.assertFalse(is_same_json(data_1, data_3))

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
