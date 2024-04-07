from boto3.dynamodb.conditions import Key, Attr
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from ddb_single.error import InvalidParameterError

# クエリ設定のENUM
from enum import Enum
from decimal import Decimal


class QueryType(Enum):
    """
    Enum for query types
    """

    EQ = "EQUAL"
    N_EQ = "NOT_EQUAL"
    IN = "IN"
    BETWEEN = "BETWEEN"
    CONTAINS = "CONTAINS"
    GT = "GREATER_THAN"
    GT_E = "GREATER_THAN_OR_EQUAL"
    LT = "LESS_THAN"
    LT_E = "LESS_THAN_OR_EQUAL"
    BEGINS = "BEGINS_WITH"
    EX = "EXISTS"
    N_EX = "NOT_EXISTS"


class FilterStatus(Enum):
    SEATCH = "search"
    STAGED = "staged"
    FILTER = "filter"


# -------
# レンジキー検索フィルター
range_expression_list = [
    QueryType.EQ,
    QueryType.BETWEEN,
    QueryType.LT,
    QueryType.LT_E,
    QueryType.GT,
    QueryType.GT_E,
    QueryType.BEGINS,
]


def is_key(mode):
    return mode in range_expression_list


def range_ex(name, value, mode):
    if mode == QueryType.EQ:
        result = Key(name).eq(value)
    elif mode == QueryType.BETWEEN:
        result = Key(name).between(min(*value), max(*value))
    elif mode == QueryType.LT:
        result = Key(name).lt(value)
    elif mode == QueryType.LT_E:
        result = Key(name).lte(value)
    elif mode == QueryType.GT:
        result = Key(name).gt(value)
    elif mode == QueryType.GT_E:
        result = Key(name).gte(value)
    elif mode == QueryType.BEGINS:
        result = Key(name).begins_with(value)
    else:
        raise InvalidParameterError(f"mode={mode} is not defined.")

    return result


# その他の変数の検索フィルター
def attr_ex(name, value, mode):
    if mode == QueryType.EQ:
        result = Attr(name).eq(value)
    elif mode == QueryType.BETWEEN:
        result = Attr(name).between(min(*value), max(*value))
    elif mode == QueryType.LT:
        result = Attr(name).lt(value)
    elif mode == QueryType.LT_E:
        result = Attr(name).lte(value)
    elif mode == QueryType.GT:
        result = Attr(name).gt(value)
    elif mode == QueryType.GT_E:
        result = Attr(name).gte(value)
    elif mode == QueryType.BEGINS:
        result = Attr(name).begins_with(value)
    elif mode == QueryType.CONTAINS:
        result = Attr(name).contains(value)
    elif mode == QueryType.IN:
        result = Attr(name).in_(value)
    elif mode == QueryType.N_EQ:
        result = Attr(name).ne(value)
    elif mode == QueryType.EX:
        result = Attr(name).exists()
    elif mode == QueryType.N_EX:
        result = Attr(name).not_exists()
    else:
        raise InvalidParameterError(f"mode={mode} is not defined.")
    return result


def attr_method(name, value, mode):
    if mode == QueryType.EQ:
        result = lambda x: x.get(name) == value  # noqa: E731
    elif mode == QueryType.BETWEEN:
        result = lambda x: min(*value) <= x.get(name) <= max(*value)  # noqa: E731
    elif mode == QueryType.LT:
        result = lambda x: x.get(name) < value  # noqa: E731
    elif mode == QueryType.LT_E:
        result = lambda x: x.get(name) <= value  # noqa: E731
    elif mode == QueryType.GT:
        result = lambda x: x.get(name) > value  # noqa: E731
    elif mode == QueryType.GT_E:
        result = lambda x: x.get(name) >= value  # noqa: E731
    elif mode == QueryType.BEGINS:
        result = lambda x: x.get(name).startswith(value)  # noqa: E731
    elif mode == QueryType.CONTAINS:
        result = lambda x: value in x.get(name)  # noqa: E731
    elif mode == QueryType.IN:
        result = lambda x: x.get(name) in value  # noqa: E731
    elif mode == QueryType.N_EQ:
        result = lambda x: x.get(name) != value  # noqa: E731
    elif mode == QueryType.EX:
        result = lambda x: name in x  # noqa: E731
    elif mode == QueryType.N_EX:
        result = lambda x: name not in x  # noqa: E731
    else:
        raise InvalidParameterError(f"mode={mode} is not defined.")
    return result


def deserialize(value):
    if isinstance(value, list):
        return [deserialize(v) for v in value]

    result = {}
    for k, v in value.items():
        if isinstance(v, dict):
            try:
                result[k] = TypeDeserializer().deserialize(v)
            except Exception:
                result[k] = deserialize(v)
        else:
            result[k] = v
    return result


def serialize(value):
    if isinstance(value, list):
        return [serialize(v) for v in value]
    return {k: TypeSerializer().serialize(v) for k, v in value.items()}


# 同じ値のJSONか調べる
def is_same_json(data_0, data_1):
    if type(data_0) is dict or type(data_1) is dict:
        keys = list(set(list(data_0.keys()) + list(data_1.keys())))
        for k in keys:
            # 値がなければFalse
            if (k not in data_1) or (k not in data_0):
                return False
            if not is_same_json(data_0.get(k), data_1.get(k)):
                return False
    elif type(data_0) is list and type(data_1) is list:
        if len(data_0) != len(data_1):
            return False
        else:
            for v_0, v_1 in zip(data_0, data_1):
                if not is_same_json(v_1, v_0):
                    return False
    else:
        return data_0 == data_1
    return True


# ユーティリティ
def json_import(data):
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            result[k] = json_import(v)
    elif isinstance(data, list):
        result = [json_import(v) for v in data]
    elif isinstance(data, float):
        result = Decimal(str(data))
    else:
        result = data
    return result


def json_export(data):
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            result[k] = json_export(v)
    elif isinstance(data, list):
        result = [json_export(v) for v in data]
    elif isinstance(data, Decimal):
        result = float(data)
    else:
        result = data
    return result
