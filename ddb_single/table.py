import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

import time
import uuid
from enum import Enum

import ddb_single.utils_botos as util_b

import logging

logger = logging.getLogger(__name__)


def default_pk_factory(model_name):
    return f"{model_name}_{uuid.uuid4().hex}"


def default_sk_factory(model_name, prefix="", suffix="_item"):
    return f"{prefix}{model_name}{suffix}"


def default_pk2model(pk):
    return pk.split("_", 1)[0]


PROJECTION_ALL = {"ProjectionType": "ALL"}


def hash_key(name):
    return {"AttributeName": name, "KeyType": "HASH"}


def range_key(name):
    return {"AttributeName": name, "KeyType": "RANGE"}


class FieldType(Enum):
    STRING = "S"
    NUMBER = "N"
    BINARY = "B"
    STRING_SET = "SS"
    NUMBER_SET = "NS"
    BINARY_SET = "BS"
    NULL = "NULL"
    BOOLEAN = "BOOL"
    MAP = "M"
    LIST = "L"


class Table:
    def __init__(
        self,
        table_name,
        primary_key="pk",
        primary_key_type="S",
        primary_key_factory=default_pk_factory,
        primary_key2model=default_pk2model,
        range_index_name="RangeIndex",
        secondary_key="sk",
        secondary_key_type="S",
        secondary_key_prefix="",
        secondary_key_suffix="_item",
        secondary_key_factory=default_sk_factory,
        unique_key="unique",
        unique_key_type="S",
        search_prefix="search_",
        relation_prefix="rel_",
        relation_joint="",
        search_data_key="data",
        search_index="DataSearchIndex",
        search_data_num_key="data-n",
        search_num_index="NumDataSearchIndex",
        search_data_bin_key="data-b",
        search_bin_index="BinDataSearchIndex",
        ReadCapacityUnits=1,
        WriteCapacityUnits=1,
        **table_kwargs,
    ):
        self.__recourse__ = boto3.resource("dynamodb", **table_kwargs)
        self.__client__ = boto3.client("dynamodb", **table_kwargs)
        self.__table_name__ = table_name

        self.__primary_key__ = primary_key
        self.__primary_key_type__ = primary_key_type
        self.__primary_key_factory__ = primary_key_factory
        self.__primary_key2model__ = primary_key2model
        self.__range_index_name__ = range_index_name
        self.__secondary_key__ = secondary_key
        self.__secondary_key_type__ = secondary_key_type
        self.__secondary_key_prefix__ = secondary_key_prefix
        self.__secondary_key_suffix__ = secondary_key_suffix
        self.__secondary_key_factory__ = secondary_key_factory
        self.__unique_key__ = unique_key
        self.__unique_key_type__ = unique_key_type
        self.__search_prefix__ = search_prefix
        self.__relation_prefix__ = relation_prefix
        self.__relation_joint__ = relation_joint
        self.__search_data_key__ = search_data_key
        self.__search_index__ = search_index
        self.__search_data_num_key__ = search_data_num_key
        self.__search_num_index__ = search_num_index
        self.__search_data_bin_key__ = search_data_bin_key
        self.__search_bin_index__ = search_bin_index
        self.__read_capacity_units__ = ReadCapacityUnits
        self.__write_capacity_units__ = WriteCapacityUnits

    def pk(self, model_name):
        return self.__primary_key_factory__(model_name)

    def pk2model(self, pk):
        return self.__primary_key2model__(pk)

    def sk(self, model_name):
        return self.__secondary_key_factory__(
            model_name, self.__secondary_key_prefix__, self.__secondary_key_suffix__
        )

    def sk2model(self, sk):
        return sk[
            len(self.__secondary_key_prefix__) : -len(  # noqa: E203
                self.__secondary_key_suffix__
            )
        ]

    def pk2sk(self, pk):
        model_name = self.pk2model(pk)
        return self.sk(model_name)

    def sk2pk(self, sk):
        model_name = self.sk2model(sk)
        return self.pk(model_name)

    def search_key_factory(self, model_name, search_key):
        return f"{self.__search_prefix__}{model_name}_{search_key}"

    def rel_prefix(self, model_name=""):
        return f"{self.__relation_prefix__}{self.__relation_joint__}{model_name}"

    def rel_key(self, pk):
        return f"{self.rel_prefix()}{pk}"

    def rel_key2pk(self, rel_key):
        return rel_key[len(f"{self.rel_prefix()}") :]  # noqa: E203

    def pk2rel_key(self, pk):
        return self.rel_key(pk)

    def search_data_key(self, type: FieldType):
        if type == FieldType.STRING:
            return self.__search_data_key__
        elif type == FieldType.NUMBER:
            return self.__search_data_num_key__
        elif type == FieldType.BINARY:
            return self.__search_data_bin_key__
        else:
            raise Exception(f"Invalid type: {type}")

    def serch_index(self, type: FieldType):
        if type == FieldType.STRING:
            return self.__search_index__
        elif type == FieldType.NUMBER:
            return self.__search_num_index__
        elif type == FieldType.BINARY:
            return self.__search_bin_index__
        else:
            raise Exception(f"Invalid type: {type}")

    # スキャン
    def _scan(self, **kwargs):
        limit = kwargs.get("Limit")
        try:
            response = self.__table__.scan(**kwargs)
        except ClientError:
            logger.error("ClientError", exc_info=True)
        else:
            if len(response["Items"]):
                res_data = response["Items"]
                while "LastEvaluatedKey" in response and len(res_data) < limit:
                    print(f"{len(res_data)}/{limit}")
                    response = self.__table__.scan(
                        **kwargs, ExclusiveStartKey=response["LastEvaluatedKey"]
                    )
                    res_data += response["Items"]
                return util_b.json_export(res_data)
            else:
                return []

    # クエリ
    def _query(self, **kwargs):
        limit = kwargs.get("Limit", float("inf"))
        try:
            response = self.__table__.query(**kwargs)
        except ClientError:
            logger.error("ClientError", exc_info=True)
        else:
            if len(response["Items"]):
                res_data = response["Items"]
                while "LastEvaluatedKey" in response and len(res_data) < limit:
                    response = self.__table__.query(
                        **kwargs, ExclusiveStartKey=response["LastEvaluatedKey"]
                    )
                    res_data += response["Items"]
                return util_b.json_export(res_data)
            else:
                return []

    # アイテムの取得
    def get_item(self, pk, sk=None):
        sk = sk if sk else self.pk2sk(pk)
        res: dict = self.__client__.get_item(
            TableName=self.__table_name__,
            Key={
                self.__primary_key__: {self.__primary_key_type__: pk},
                self.__secondary_key__: {self.__secondary_key_type__: sk},
            },
        )
        if "Item" not in res:
            # アイテムがない場合はNoneを返す
            return None
        res = util_b.deserialize(res.get("Item"))
        res = util_b.json_export(res)
        return res

    # アイテムをバッチで取得
    def _batch_get_item(self, key_list: list, sleep_time=0.5, max_tries=5) -> list:
        # リストが空なら空リストを返す
        if not key_list or len(key_list) == 0:
            return []

        table_name = self.__table_name__
        key_list = [
            {
                self.__primary_key__: {
                    self.__primary_key_type__: k[self.__primary_key__]
                },
                self.__secondary_key__: {
                    self.__secondary_key_type__: k[self.__secondary_key__]
                },
            }
            for k in key_list
        ]

        tries = 0
        dynamo_table_data = []
        batch_keys = {table_name: {"Keys": key_list}}

        while tries < max_tries:
            batch_get_item_response = self.__client__.batch_get_item(
                RequestItems=batch_keys
            )
            dynamo_table_data += batch_get_item_response["Responses"].get(
                table_name, []
            )
            unprocessed_key = batch_get_item_response["UnprocessedKeys"]
            if unprocessed_key:
                batch_keys = unprocessed_key

                # 指数関数的に待機
                tries += 1
                time.sleep(sleep_time)
                sleep_time = min(sleep_time * 2, 8)
            else:
                break

        res = util_b.deserialize(dynamo_table_data)
        res = util_b.json_export(res)
        return res

    # アイテムをバッチで取得
    def batch_get(self, keys):
        MAX_LENGTH = 100
        res = []
        for i in range(0, len(keys), MAX_LENGTH):
            res += self._batch_get_item(keys[i : i + MAX_LENGTH])  # noqa: E203
        return res

    # pksからアイテムをバッチで取得
    def batch_get_from_pks(self, pks: list) -> list:
        keys = [
            {self.__primary_key__: pk, self.__secondary_key__: self.pk2sk(pk)}
            for pk in pks
        ]
        return self.batch_get(keys)

    # --- 検索関連 ---
    # 関連先を検索
    def relation(self, pk, model_name="", field_name="", pk_only=False):
        logger.debug(f"pk: {pk}, model_name: {model_name}, field_name: {field_name}")
        KeyConditionExpression = Key(self.__primary_key__).eq(pk)
        if model_name:
            KeyConditionExpression &= Key(self.__secondary_key__).begins_with(
                self.rel_prefix(model_name)
            )
        if field_name:
            # フィールドの指定がある場合
            res = self._query(
                KeyConditionExpression=KeyConditionExpression,
                FilterExpression=Attr(self.__search_data_key__).eq(field_name),
            )
        else:
            # モデルの指定がある場合
            res = self._query(KeyConditionExpression=KeyConditionExpression)
        pks = [self.rel_key2pk(r[self.__secondary_key__]) for r in res]
        if pk_only:
            return pks
        else:
            return self.batch_get_from_pks(pks)

    # 関連元を検索
    def reference(self, pk, model_name="", field_name="", pk_only=False):
        logger.debug(f"pk: {pk}, model_name: {model_name}, field_name: {field_name}")
        KeyConditionExpression = Key(self.__secondary_key__).eq(self.rel_key(pk))
        if field_name:
            # フィールドの指定がある場合
            res = self._query(
                KeyConditionExpression=KeyConditionExpression
                & Key(self.__search_data_key__).eq(field_name),
                FilterExpression=Attr(self.__primary_key__).begins_with(model_name),
                IndexName=self.__search_index__,
            )
        elif model_name:
            # モデルの指定がある場合
            res = self._query(
                KeyConditionExpression=KeyConditionExpression
                & Key(self.__primary_key__).begins_with(model_name),
                IndexName=self.__range_index_name__,
            )
        else:
            # フィールド・モデルの指定がない場合
            res = self._query(
                KeyConditionExpression=KeyConditionExpression,
                IndexName=self.__range_index_name__,
            )
        pks = [r[self.__primary_key__] for r in res]
        if pk_only:
            return pks
        else:
            return self.batch_get_from_pks(pks)

    # フィルター
    def filter(self, items, searchExs):
        if not searchExs:
            return items
        res = []
        for item in items:
            for searchEx in searchExs:
                if searchEx["FilterMethod"](item):
                    res.append(item)
                    break
        return res

    # 検索
    def search(self, model_name, *searchEx, pk_only=False, limit=None):
        simple_ex = [
            s for s in searchEx if s["FilterStatus"] == util_b.FilterStatus.SEATCH
        ]
        staged_ex = [
            s for s in searchEx if s["FilterStatus"] == util_b.FilterStatus.STAGED
        ]
        filter_ex = [
            s for s in searchEx if s["FilterStatus"] == util_b.FilterStatus.FILTER
        ]
        if staged_ex:
            logger.debug(f"staged_ex: {staged_ex}")
            res = set()
            all_items = []
            for i, searchEx in enumerate(staged_ex):
                _res = (
                    self._query(
                        KeyConditionExpression=searchEx["KeyConditionExpression"],
                        IndexName=searchEx["IndexName"],
                    )
                    or []
                )
                all_items += _res
                _res = [r[self.__primary_key__] for r in _res]
                if i:
                    res &= set(_res)
                else:
                    res = set(_res)
        else:
            # シンプルにクエリ検索
            logger.debug(f"simple_ex: {simple_ex}")
            KeyConditionExpression = Key(self.__secondary_key__).eq(self.sk(model_name))
            for ex in simple_ex:
                KeyConditionExpression &= ex["KeyConditionExpression"]
            if filter_ex:
                # フィルタがあれば追加
                FilterExpression = filter_ex[0]["FilterExpression"]
                for ex in filter_ex[1:]:
                    FilterExpression &= ex["FilterExpression"]
                res = (
                    self._query(
                        KeyConditionExpression=KeyConditionExpression,
                        FilterExpression=FilterExpression,
                        IndexName=self.__range_index_name__,
                    )
                    or []
                )
            else:
                # フィルタがなければ全件検索
                logger.debug("FilterExpression not found")
                res = (
                    self._query(
                        KeyConditionExpression=KeyConditionExpression,
                        IndexName=self.__range_index_name__,
                    )
                    or []
                )
        if limit is not None:
            res = list(res)[:limit]
        if pk_only and filter_ex:
            return list(res)
        elif staged_ex:
            logger.debug(f"batch_get: {res}")
            res = self.batch_get_from_pks(list(res))
            #  filter_ex があればフィルタ
            res = self.filter(res, filter_ex)
        if pk_only:
            return [r[self.__primary_key__] for r in res]
        return res

    # --- 更新関連 ---
    # バッチライター
    def batch_writer(self):
        return self.__table__.batch_writer()

    # アイテムの作成
    def create(self, item, batch=None):
        item = util_b.json_import(item)
        table = batch or self.__table__
        table.put_item(Item=item)
        return item

    # アイテムの更新
    def update(self, item, batch=None, old_item=None):
        is_changed = False
        item = util_b.json_import(item)
        if not old_item and not batch:
            # 単一の処理で、既存のアイテムがない場合は、既存のアイテムを取得する
            old_item = self.get_item(
                item[self.__primary_key__], item[self.__secondary_key__]
            )
        if old_item:
            new_item = {**old_item, **item}
            if not util_b.is_same_json(old_item, new_item):
                self.create(new_item, batch)
                is_changed = True
            return new_item, is_changed
        else:
            self.create(item, batch)
            return item, is_changed

    # 作成のバッチ処理
    def batch_create(self, items, batch=None):
        items = util_b.json_import(items)
        if batch:
            for item in items:
                batch.put_item(Item=item)
        else:
            with self.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)
        return items

    # 更新のバッチ処理
    def batch_update(self, items, batch=None):
        items = util_b.json_import(items)
        old_items = self.batch_get(items)
        new_items = []
        for item in items:
            old_item = [
                i
                for i in old_items
                if i[self.__primary_key__] == item[self.__primary_key__]
            ]
            if old_item:
                old_item = old_item[0]
                new_item = {**old_item, **item} if old_item else item
                if not util_b.is_same_json(old_item, new_item):
                    new_items.append(new_item)
        self.batch_create(new_items, batch)
        return new_items

    # --- 削除関連 ---
    # アイテムの削除
    def delete(self, pk, sk, batch=None):
        table = batch or self.__table__
        table.delete_item(Key={self.__primary_key__: pk, self.__secondary_key__: sk})

    def detele_item(self, item, batch=None):
        self.delete(item[self.__primary_key__], item[self.__secondary_key__], batch)

    # バッチ処理
    def batch_delete_items(self, items, batch=None):
        logger.debug(f"batch_delete_items: {items}")
        if batch:
            for item in items:
                self.detele_item(item, batch)
        else:
            with self.batch_writer() as batch:
                for item in items:
                    self.detele_item(item, batch)

    # アイテムを全削除
    def clear_item(self, pk, batch=None):
        # メインアイテム・検索アイテム・関連アイテムを削除
        items_main = self._query(
            KeyConditionExpression=Key(self.__primary_key__).eq(pk),
        )
        # 参照アイテムを削除
        items_ref = self._query(
            KeyConditionExpression=Key(self.__secondary_key__).eq(self.pk2rel_key(pk)),
            IndexName=self.__range_index_name__,
        )
        # まとめて削除
        items = items_main + items_ref
        self.batch_delete_items(items, batch)

    # 関連付けを削除
    def clear_relation(self, pk, model_name="", batch=None):
        KeyConditionExpression = Key(self.__primary_key__).eq(pk)
        if model_name:
            KeyConditionExpression &= Key(self.__secondary_key__).begins_with(
                self.rel_prefix(model_name)
            )
        items = self._query(KeyConditionExpression=KeyConditionExpression)
        self.batch_delete_items(items, batch)

    # 参照を削除
    def clear_reference(self, pk, model_name="", batch=None):
        KeyConditionExpression = Key(self.__secondary_key__).eq(self.pk2rel_key(pk))
        if model_name:
            KeyConditionExpression &= Key(self.__primary_key__).begins_with(model_name)
        items = self._query(
            KeyConditionExpression=KeyConditionExpression,
            IndexName=self.__range_index_name__,
        )
        self.batch_delete_items(items, batch)

    # --- ここからテーブル作成 ---
    def init(self):
        self.__table__ = self.__recourse__.Table(self.__table_name__)
        try:
            self.__table__.table_status
        except ClientError:
            self.create_table()

    def create_table(self):
        # キースキーマのプリセット
        throughput = {
            "ReadCapacityUnits": self.__read_capacity_units__,
            "WriteCapacityUnits": self.__read_capacity_units__,
        }

        # スライド関連のテーブル
        self.__recourse__.create_table(
            TableName=self.__table_name__,
            KeySchema=[
                hash_key(self.__primary_key__),
                range_key(self.__secondary_key__),
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": self.__primary_key__,
                    "AttributeType": self.__primary_key_type__,
                },
                {
                    "AttributeName": self.__secondary_key__,
                    "AttributeType": self.__secondary_key_type__,
                },
                {"AttributeName": self.__search_data_key__, "AttributeType": "S"},
                {"AttributeName": self.__search_data_num_key__, "AttributeType": "N"},
                {"AttributeName": self.__search_data_bin_key__, "AttributeType": "B"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": self.__range_index_name__,
                    "KeySchema": [
                        hash_key(self.__secondary_key__),
                        range_key(self.__primary_key__),
                    ],
                    "Projection": PROJECTION_ALL,
                    "ProvisionedThroughput": throughput,
                },
                {
                    "IndexName": self.__search_index__,
                    "KeySchema": [
                        hash_key(self.__secondary_key__),
                        range_key(self.__search_data_key__),
                    ],
                    "Projection": PROJECTION_ALL,
                    "ProvisionedThroughput": throughput,
                },
                {
                    "IndexName": self.__search_num_index__,
                    "KeySchema": [
                        hash_key(self.__secondary_key__),
                        range_key(self.__search_data_num_key__),
                    ],
                    "Projection": PROJECTION_ALL,
                    "ProvisionedThroughput": throughput,
                },
                {
                    "IndexName": self.__search_bin_index__,
                    "KeySchema": [
                        hash_key(self.__secondary_key__),
                        range_key(self.__search_data_bin_key__),
                    ],
                    "Projection": PROJECTION_ALL,
                    "ProvisionedThroughput": throughput,
                },
            ],
            ProvisionedThroughput=throughput,
        )
