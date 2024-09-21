# ddb_single/utils_botos.py
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
    func_mapping = {
        QueryType.EQ: lambda n, v: Key(n).eq(v),
        QueryType.BETWEEN: lambda n, v: Key(n).between(min(*v), max(*v)),
        QueryType.LT: lambda n, v: Key(n).lt(v),
        QueryType.LT_E: lambda n, v: Key(n).lte(v),
        QueryType.GT: lambda n, v: Key(n).gt(v),
        QueryType.GT_E: lambda n, v: Key(n).gte(v),
        QueryType.BEGINS: lambda n, v: Key(n).begins_with(v),
    }
    try:
        result = func_mapping[mode](name, value)
    except KeyError as err:
        raise InvalidParameterError(f"mode={mode} is not defined.") from err
        raise InvalidParameterError(f"mode={mode} is not defined.")
    return result


# その他の変数の検索フィルター
def attr_ex(name, value, mode):
    func_mapping = {
        QueryType.EQ: lambda n, v: Attr(n).eq(v),
        QueryType.BETWEEN: lambda n, v: Attr(n).between(min(*v), max(*v)),
        QueryType.LT: lambda n, v: Attr(n).lt(v),
        QueryType.LT_E: lambda n, v: Attr(n).lte(v),
        QueryType.GT: lambda n, v: Attr(n).gt(v),
        QueryType.GT_E: lambda n, v: Attr(n).gte(v),
        QueryType.BEGINS: lambda n, v: Attr(n).begins_with(v),
        QueryType.CONTAINS: lambda n, v: Attr(n).contains(v),
        QueryType.IN: lambda n, v: Attr(n).is_in(v),
        QueryType.N_EQ: lambda n, v: Attr(n).ne(v),
        QueryType.EX: lambda n, v: Attr(n).exists(),
        QueryType.N_EX: lambda n, v: Attr(n).not_exists(),
    }
    try:
        result = func_mapping[mode](name, value)
    except KeyError as err:
        raise InvalidParameterError(f"mode={mode} is not defined.") from err
        raise InvalidParameterError(f"mode={mode} is not defined.")
    return result


def attr_method(name, value, mode):
    func_mapping = {
        QueryType.EQ: lambda x: x.get(name) == value,
        QueryType.BETWEEN: lambda x: min(*value) <= x.get(name) <= max(*value),
        QueryType.LT: lambda x: x.get(name) < value,
        QueryType.LT_E: lambda x: x.get(name) <= value,
        QueryType.GT: lambda x: x.get(name) > value,
        QueryType.GT_E: lambda x: x.get(name) >= value,
        QueryType.BEGINS: lambda x: x.get(name).startswith(value),
        QueryType.CONTAINS: lambda x: value in x.get(name),
        QueryType.IN: lambda x: x.get(name) in value,
        QueryType.N_EQ: lambda x: x.get(name) != value,
        QueryType.EX: lambda x: name in x,
        QueryType.N_EX: lambda x: name not in x,
    }
    result = func_mapping.get(mode)
    if result is None:
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
