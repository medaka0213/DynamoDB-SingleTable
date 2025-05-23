from decimal import Decimal
from boto3.dynamodb.conditions import Key

from ddb_single.table import FieldType, Table, SearchExpression
import ddb_single.utils_botos as util_b
from ddb_single.error import ValidationError

import logging

logger = logging.getLogger(__name__)


class DBField:
    """
    DBField is a field of a model. It is used to define the structure of a model.
    """

    __setup__ = False

    def __init__(
        self,
        type: FieldType = FieldType.STRING,
        default=None,
        default_factory=None,
        nullable=True,
        required=False,
        primary_key=False,
        secondary_key=False,
        unique_key=False,
        search_key=False,
        reletion=None,
        reletion_by_unique=True,
        relation_raise_if_not_found=False,
        ignore_case=False,
        **kwargs,
    ):
        """
        Args:
            type (FieldType): The type of the field.
            default: The default value of the field.
            default_factory: The default factory of the field.
            nullable (bool): Whether the field can be null.
            required (bool): Whether the field is required.
            primary_key (bool): Whether the field is a primary key.
            secondary_key (bool): Whether the field is a secondary key.
            unique_key (bool): Whether the field is a unique key.
            search_key (bool): Whether the field is a search key.
            reletion (BaseModel): The reletion model of the field.
            reference (BaseModel): The reference model of the field.
            reletion_by_unique (bool): Whether the reletion is by unique key.
            relation_raise_if_not_found (bool): Whether to raise an error if the relation is not found.
        """
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
        self.reletion_by_unique = reletion_by_unique
        self.relation_raise_if_not_found = relation_raise_if_not_found
        self.ignore_case = ignore_case
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
        """
        Returns:
            bool: Whether the field is a list.
        """
        return self.type in [
            FieldType.LIST,
            FieldType.STRING_SET,
            FieldType.NUMBER_SET,
            FieldType.BINARY_SET,
        ]

    def describe(self):
        return {
            "type": self.type.name,
            "nullable": self.nullable,
            "primary_key": self.primary_key,
            "secondary_key": self.secondary_key,
            "unique_key": self.unique_key,
            "search_key": self.search_key,
            "relation": self.relation.__model_name__ if self.relation else None,
            "reletion_by_unique": self.reletion_by_unique,
            "ignore_case": self.ignore_case,
        }

    def validate(self, value=None, skip=False):
        """
        値をバリデーションして、フィールドの値を設定
        Args:
            value: The value to be validated. If not provided, the value of the field will be used.
        Returns:
            The validated value.
        """
        # 先に必ずクリア
        self.value = None
        self.__setup__ = True

        if value is not None:
            self.value = value
        elif self.default is not None:
            self.value = self.default
        elif self.default_factory:
            self.value = self.default_factory(self.__model_cls__)
        else:
            # どれもなければ None を明示
            self.value = None

        if not skip:
            if value is None:
                if not self.nullable:
                    raise ValidationError(f"Not nullable: {self.__class__.__name__}")
            else:
                self._setup_relation()
                self.value = self._validate_value(self.value)
        return self.value

    def _setup_relation(self):
        def extract_value(v, by_unique):
            types = str, bytes, int, float, Decimal, bool
            if not [t for t in types if isinstance(v, t)]:
                if by_unique:
                    return v.data[self.value.__unique_keys__[0]]
                else:
                    return v.data[self.value.__primary_key__]
            else:
                return v

        if not self.is_list():
            if self.relation:
                self.value = extract_value(self.value, self.reletion_by_unique)
        else:
            if self.relation:
                self.value = [
                    extract_value(v, self.reletion_by_unique) for v in self.value
                ]
        return self.value

    def _validate_value(self, value):
        field_name = getattr(self, "name", "DBField")
        if self.is_list():
            if not isinstance(value, list):
                raise ValidationError(
                    f"{field_name} must be a list: {self.type} != {type(value)}, input={str(value)[:100]}"
                )
            try:
                if self.type == FieldType.LIST:
                    return value
                elif self.type == FieldType.STRING_SET:
                    return set(value)
                elif self.type == FieldType.NUMBER_SET:
                    return set(map(Decimal, str(value)))
                elif self.type == FieldType.BINARY_SET:
                    return set(map(bytes, str(value)))
                return value
            except Exception as e:
                logger.info("Failed to validate", exc_info=e)
                raise ValidationError(
                    f"{field_name} must be a valid list: {self.type} != {type(value)}, input={str(value)[:100]}"
                )
        else:
            try:
                if isinstance(value, list):
                    raise ValidationError(
                        f"{field_name} must not be a list: {self.type} != {type(value)}, input={str(value)[:100]}"
                    )
                if self.type == FieldType.STRING:
                    return str(value)
                elif self.type == FieldType.NUMBER:
                    return Decimal(str(value))
                elif self.type == FieldType.BINARY:
                    if isinstance(value, str):
                        return value.encode("utf-8")
                    else:
                        return bytes(value)
                elif self.type == FieldType.BOOLEAN:
                    return bool(value)
                return value
            except Exception as e:
                logger.info("Failed to validate", exc_info=e)
                raise ValidationError(
                    f"Value {field_name} must be a valid value, {self.type} != {type(value)}, input={str(value)[:100]}"
                )

    def search_key_factory(self):
        """
        Returns:
            str: The search key of the field.
        """
        return self.__table__.search_key_factory(
            self.__model_cls__.__model_name__, self.name
        )

    def search_data_key(self):
        """
        Returns:
            str: The search data key of the field.
        """
        return self.__table__.search_data_key(self.type)

    def search_index(self):
        """
        Returns:
            str: The search index of the field.
        """
        return self.__table__.search_index(self.type)

    def search_item(self, pk):
        """
        Args:
            pk: The primary key of the item.
        Returns:
            dict: The search item.
        """
        _value = self.value
        if self.ignore_case and isinstance(_value, str):
            # lower case if self.ignore_case = True
            _value = _value.lower()
        return {
            self.__table__.__primary_key__: pk,
            self.__table__.__secondary_key__: self.search_key_factory(),
            self.search_data_key(): _value,
        }

    def key_ex(self, value, mode):
        """
        Args:
            value: The value to be compared.
            mode: The mode of the comparison.
        Returns:
            dict: The key expression.
        """
        if mode in {util_b.QueryType.BETWEEN, util_b.QueryType.IN}:
            value = [
                (
                    v.lower()  # 大文字小文字を無視する場合
                    if self.ignore_case and isinstance(v, str)
                    else v
                )
                for v in [self._validate_value(v) for v in value]
            ]
        else:
            value = self._validate_value(value)
            if self.ignore_case and isinstance(value, str):
                # 大文字小文字を無視する場合
                value = value.lower()
        if self.secondary_key:
            raise ValidationError(
                f"Secondary key should not be used as a key: {self.name}"
            )

        if util_b.is_key(mode):
            if self.primary_key:
                # PKを使う場合
                logger.debug(
                    f"KeyConditionExpression [primary key]: {self.name} = {value}, {mode}"
                )
                return SearchExpression(
                    FilterMethod=util_b.attr_method(self.name, value, mode),
                    KeyConditionExpression=util_b.range_ex(self.name, value, mode),
                    FilterStatus=util_b.FilterStatus.SEARCH,
                )
            elif self.search_key and value:
                # SearchKeyを使う場合
                KeyConditionExpression = Key(self.__table__.__secondary_key__).eq(
                    self.search_key_factory()
                ) & util_b.range_ex(self.search_data_key(), value, mode)
                logger.debug(
                    f"KeyConditionExpression [search key]: {self.search_data_key()} = {value}, {mode}"
                )
                return SearchExpression(
                    FilterMethod=util_b.attr_method(self.name, value, mode),
                    KeyConditionExpression=KeyConditionExpression,
                    IndexName=self.search_index(),
                    FilterStatus=util_b.FilterStatus.STAGED,
                )
        elif self.search_key:
            # SearchKeyを使うが、Queryで使えない方法で検索する場合
            logger.debug(
                f"FilterExpression [search key]: {self.search_data_key()} = {value}, {mode}"
            )
            return SearchExpression(
                FilterMethod=util_b.attr_method(self.name, value, mode),
                KeyConditionExpression=Key(self.__table__.__secondary_key__).eq(
                    self.search_key_factory()
                ),
                IndexName=self.__table__.__range_index_name__,
                FilterExpression=util_b.attr_ex(self.search_data_key(), value, mode),
                FilterStatus=util_b.FilterStatus.FILTER_STAGED,
            )
        # SearchKeyを使わない場合
        logger.debug(f"FilterExpression: {self.name} = {value}, {mode}")
        return SearchExpression(
            FilterMethod=util_b.attr_method(self.name, value, mode),
            FilterExpression=util_b.attr_ex(self.name, value, mode),
            FilterStatus=util_b.FilterStatus.FILTER,
        )

    def eq(self, value):
        """
        Args:
            value: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.EQ.
        """
        return self.key_ex(value, util_b.QueryType.EQ)

    def ne(self, value):
        """
        Args:
            value: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.NE.
        """
        return self.key_ex(value, util_b.QueryType.N_EQ)

    def lt(self, value):
        """
        Args:
            value: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.LT.
        """
        return self.key_ex(value, util_b.QueryType.LT)

    def lte(self, value):
        """
        Args:
            value: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.LTE.
        """
        return self.key_ex(value, util_b.QueryType.LT_E)

    def gt(self, value):
        """
        Args:
            value: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.GT.
        """
        return self.key_ex(value, util_b.QueryType.GT)

    def gte(self, value):
        """
        Args:
            value: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.GTE.
        """
        return self.key_ex(value, util_b.QueryType.GT_E)

    def between(self, value1, value2):
        """
        Args:
            value1: The value to be compared.
            value2: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.BETWEEN.
        """
        return self.key_ex((value1, value2), util_b.QueryType.BETWEEN)

    def begins_with(self, value):
        """
        Args:
            value: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.BEGINS_WITH.
        """
        return self.key_ex(value, util_b.QueryType.BEGINS)

    def contains(self, value):
        """
        Args:
            value: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.CONTAINS.
        """
        return self.key_ex(value, util_b.QueryType.CONTAINS)

    def in_(self, value):
        """
        Args:
            value: The value to be compared.
        Returns:
            dict: key_ex with mode QueryType.IN.
        """
        return self.key_ex(value, util_b.QueryType.IN)


class BaseModel:
    """
    The base model class.
    Examples:
        >>> class User(BaseModel):
        ...     __table__ = table
        ...     __model_name__ = "user"
        ...     id = DBField(primary_key=True, required=True)
        ...     name = DBField(required=True)
        ...     age = DBField(type=FieldType.NUMBER)
    """

    __setup__ = False
    __use_unique_for_relations__ = True
    __model_name__: str = None
    __table__: Table = None

    def __init__(self, __skip_validation__=False, **kwargs):
        self._setup()
        self.data = {}
        for k, v in self.__class__.__dict__.items():
            if isinstance(v, DBField):
                self.data[k] = v.validate(kwargs.get(k), __skip_validation__)

    def _setup(self):
        if not self.__table__:
            raise ValidationError("Table not set")
        if not self.__model_name__:
            raise ValidationError("Not set model name")
        self.data = {}
        self.__search_keys__ = []
        self.__unique_keys__ = []
        self.__primary_key__ = self.__table__.__primary_key__
        self.__secondary_key__ = self.__table__.__secondary_key__
        self.__relation_keys__ = []
        self.__reference_keys__ = []
        setattr(
            self.__class__,
            self.__primary_key__,
            DBField(primary_key=True, default=self.__table__.pk(self.__model_name__)),
        )
        setattr(
            self.__class__,
            self.__secondary_key__,
            DBField(secondary_key=True, default=self.__table__.sk(self.__model_name__)),
        )
        for k, v in self.__class__.__dict__.items():
            if isinstance(v, DBField):
                v.setup(k, self)
                if v.unique_key:
                    self.__unique_keys__.append(k)
                if v.search_key or v.unique_key:
                    self.__search_keys__.append(k)
                if v.relation:
                    self.__relation_keys__.append(k)
        if not self.__unique_keys__ and self.__use_unique_for_relations__:
            raise ValidationError(
                f"Missing unique keys for relation: {self.__model_name__}"
            )
        self.__setup__ = True

    def get_field(self, key: str) -> DBField:
        """
        Args:
            key: DBField name.
        Returns:
            DBField: DBField instance.
        """
        res = self.__class__.__dict__.get(key)
        logger.debug(f"__getitem__ {res}")
        if isinstance(res, DBField):
            return res
        raise KeyError(f"Key {key} not found")

    @classmethod
    def describe(cls):
        """
        Returns:
            dict: The description of the model.
        """
        fields = {}
        for k, v in cls.__dict__.items():
            if isinstance(v, DBField):
                fields[k] = v.describe()
        return {
            "model_name": cls.__model_name__,
            "table_name": cls.__table__.__table_name__,
            "fields": fields,
        }
