from statistics import mode
import boto3
from boto3.dynamodb.conditions import Key, Attr

from ddb_single.table import FieldType, Table
import ddb_single.utils_botos as util_b


class DBField:
    __setup__ = False
    def __init__(self, type:FieldType=FieldType.STRING, default=None, default_factory=None, nullable=True, required=False, 
                 primary_key=False, secondary_key=False, unique_key=False, search_key=False, 
                 reletion=None, reference=None, reletion_by_unique=True, reference_by_unique=True,
                 **kwargs):
        self.type = type
        self.default = default
        self.default_factory = default_factory
        self.nullable = nullable
        self.required = required
        self.primary_key = primary_key
        self.secondary_key = secondary_key
        self.unique_key = unique_key
        self.search_key = search_key or unique_key
        self.relation = reletion
        self.reference = reference
        self.reletion_by_unique = reletion_by_unique
        self.reference_by_unique = reference_by_unique
        self.value = None
    
    def setup(self, name, model_cls):
        self.__model_cls__ = model_cls
        self.__table__: Table = model_cls.__table__
        self.name = name
        if self.primary_key:
            self.default = None
            self.default_factory = lambda x: self.__table__.pk(model_cls.__model_name__)
        if self.secondary_key:
            self.default = None
            self.default_factory = lambda x: self.__table__.sk(model_cls.__model_name__)
    
    def is_list(self):
        return self.type in [FieldType.LIST, FieldType.STRING_SET, FieldType.NUMBER_SET, FieldType.BINARY_SET]

    def validate(self, value=None):
        self.__setup__ = True
        if value is not None:
            self.value = value
        elif self.default:
            self.value = self.default
        elif self.default_factory:
            self.value = self.default_factory(self.__model_cls__)
        else:
            if not self.nullable:
                raise ValueError(f"Not nullable: {self.__class__.__name__}")
        return self.value

    def search_key_factory(self):
        return self.__table__.search_key_factory(self.__model_cls__.__model_name__, self.name)

    def search_data_key(self):
        return self.__table__.search_data_key(self.type)

    def serch_index(self):
        return self.__table__.serch_index(self.type)

    def search_item(self, pk):
        return {
            self.__table__.__primary_key__: pk,
            self.__table__.__secondary_key__: self.search_key_factory(),
            self.search_data_key(): self.value,
        }
    
    def key_ex(self, value, mode):
        if self.secondary_key:
            raise ValueError(f"Secondary key can not be used as a key: {self.name}")
        res = {
            "FilterMethod": util_b.attr_method(self.name, value, mode),
        }
        if util_b.is_key(mode):
            if self.primary_key:
                return {**res,
                    "KeyConditionExpression": util_b.range_ex(self.name, value, mode),
                    "FilterStatus": util_b.FilterStatus.SEATCH
                }
            elif self.search_key:
                KeyConditionExpression = Key(self.__table__.__secondary_key__).eq(self.search_key_factory()) \
                    & util_b.range_ex(self.search_data_key(), value, mode)
                return {**res,
                    "KeyConditionExpression": KeyConditionExpression,
                    "IndexName": self.serch_index(),
                    "FilterStatus": util_b.FilterStatus.STAGED
                }
        return {**res,
            "FilterExpression": util_b.attr_ex(self.name, value, mode),
            "FilterStatus": util_b.FilterStatus.FILTER
        }
    
    def eq(self, value):
        return self.key_ex(value, util_b.QueryType.EQ)

class BaseModel():
    __setup__ = False
    __use_unique_for_relations__ = True
    __model_name__:str = None
    __table__: Table = None

    def __init__(self, **kwargs):
        self._setup()
        self.data = {}
        for k, v in self.__class__.__dict__.items():
            if isinstance(v, DBField):
                self.data[k] = v.validate(kwargs.get(k))
                if v.required and not k in kwargs:
                    raise ValueError(f"Missing required field: {k}")

    def _setup(self):
        if not self.__table__:
            raise ValueError("Table not set")
        if not self.__model_name__:
            raise ValueError("Not set model name")
        self.data = {}
        self.__search_keys__ = []
        self.__unique_keys__ = []
        self.__primary_key__ = None
        self.__secondary_key__ = None
        self.__relation_keys__ = []
        self.__reference_keys__ = []
        for k, v in self.__class__.__dict__.items():
            if isinstance(v, DBField):
                v.setup(k, self)
                if v.primary_key:
                    if not self.__primary_key__:
                        self.__primary_key__ = k
                    else:
                        raise ValueError(f"Duplicate primary key: {k}")
                if v.secondary_key:
                    if not self.__secondary_key__:
                        self.__secondary_key__ = k
                    else:
                        raise ValueError(f"Duplicate secondary key: {k}")
                if v.unique_key:
                    self.__unique_keys__.append(k)
                if v.search_key or v.unique_key:
                    self.__search_keys__.append(k)
                if v.relation:
                    self.__relation_keys__.append(k)
                if v.reference:
                    self.__reference_keys__.append(k)
        if not self.__primary_key__:
            raise ValueError(f"Missing primary key: {self.__model_name__}")
        if not self.__secondary_key__:
            raise ValueError(f"Missing secondary key: {self.__model_name__}")
        if not self.__unique_keys__ and self.__use_unique_for_relations__:
            raise ValueError(f"Missing unique keys for relation: {self.__model_name__}")
        self.__setup__ = True
    
    def get_unique_key(self):
        return self.__unique_keys__[0]

    def get_unique_value(self):
        return self.data[self.get_unique_key()]
