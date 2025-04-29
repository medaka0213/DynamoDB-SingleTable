from typing import Optional, List
from ddb_single.model import BaseModel, DBField
from ddb_single.table import Table
import ddb_single.utils_botos as util_b
from ddb_single.error import ValidationError, NotFoundError

import logging

logger = logging.getLogger(__name__)


class Query:
    def __init__(self, table: Table, model: Optional[BaseModel] = None):
        self.__table__ = table
        if model:
            self.model(model)

    def model(self, model: BaseModel):
        """
        Set DB data model.
        Args:
            model (BaseModel): DB data model
        """
        if not model.__setup__:
            model = model(__skip_validation__=True)
        self.__model__ = model
        return self

    def get_pk(self):
        return self.__model__.data[self.__model__.__primary_key__]

    def get_unique(self):
        return self.__model__.data[self.__model__.__unique_keys__[0]]

    def _search_items(self):
        items_add = []
        items_remove = []
        for k in self.__model__.__search_keys__:
            field: DBField = self.__model__.__class__.__dict__[k]
            if k in self.__model__.data.keys() and field.value:
                items_add.append(
                    field.search_item(
                        self.__model__.data[self.__model__.__primary_key__]
                    )
                )
            else:
                items_remove.append(
                    field.search_item(
                        self.__model__.data[self.__model__.__primary_key__]
                    )
                )
        return items_add, items_remove

    # 検索
    def search(self, *queries, pk_only=False, limit=None):
        """
        Search items.
        Args:
            queries (List[dict]): Query objects
        """
        return self.__table__.search(
            self.__model__.__model_name__, *queries, pk_only=pk_only, limit=limit
        )

    def get(self, pk: str):
        """
        アイテムを取得
        Args:
            pk: Primary key
        """
        res = self.__table__.get_item(pk)
        return res

    def get_by_unique(
        self, value, pk_only=False, keys: List[str | DBField] = None
    ) -> dict:
        """
        ユニークキーで取得
        Args:
            value: Unique key value
            keys: Unique key. If not specified, search by all unique keys.
        """
        if keys is None:
            keys = []
        specified_keys: List[str] = []
        for key in keys:
            # key が文字列ならそのまま、DBField なら name を取得
            if isinstance(key, str):
                specified_keys.append(key)
            else:
                specified_keys.append(key.name)

        res = []
        for key in self.__model__.__unique_keys__:
            if specified_keys and key not in specified_keys:
                # 指定されたキー以外はスキップ
                logger.warning(f"get_by_unique: {key} not in {specified_keys} ... skip")
                continue
            _res = self.search(
                getattr(self.__model__.__class__, key).eq(value), pk_only=pk_only
            )
            logger.debug(f"get_by_unique: {key}={value} result={_res}")
            res.extend(_res)
        if res:
            return res[0]
        return None

    def batch_get(self, pks: List[str]):
        """
        プライマリキーのリストから一括取得
        Args:
            pks: Primary keys
        """
        res = self.__table__.batch_get_from_pks(pks)
        return res

    def batch_get_by_unique(
        self, uniques: List[str], pk_only=False, keys: List[str | DBField] = None
    ):
        """
        ユニークキーのリストから一括取得
        Args:
            pks: Primary keys
        """
        if keys is None:
            keys = []
        specified_keys: List[str] = []
        for key in keys:
            # key が文字列ならそのまま、DBField なら name を取得
            if isinstance(key, str):
                specified_keys.append(key)
            else:
                specified_keys.append(key.name)
        res = []
        for key in self.__model__.__unique_keys__:
            if specified_keys and key not in specified_keys:
                # 指定されたキー以外はスキップ
                logger.warning(
                    f"batch_get_by_unique: {key} not in {specified_keys} ... skip"
                )
                continue
            _res = self.search(
                getattr(self.__model__.__class__, key).in_(uniques), pk_only=pk_only
            )
            logger.debug(f"batch_get_by_unique: {key} in {uniques} result={_res}")
            res.extend(_res)
        return res

    def validate(self):
        for k, v in self.__model__.data.items():
            if k in self.__model__.__search_keys__:
                field: DBField = self.__model__.__class__.__dict__[k]
                field.validate(v)

    def create(self, batch=None, raise_if_exists=False):
        """
        アイテムを新規作成
        Args:
            batch: BatchWriteItem
            raise_if_exists (bool): Throw ValidationError if item already exists
        """
        old_item = self.get_by_unique(
            self.__model__.data[self.__model__.__unique_keys__[0]]
        )
        if old_item:
            if raise_if_exists:
                raise ValidationError("Item Already exists")
            else:
                self._update(old_item, new_item={}, batch=batch)
        else:
            self._create(batch)

    def update(self, target: dict = None, batch=None):
        """
        アイテムを更新
        Args:
            target: Target item
            batch: BatchWriteItem
        """
        payload = self.get_by_unique(
            self.__model__.data[self.__model__.__unique_keys__[0]]
        )
        if payload:
            self._update(payload, target or {}, batch=batch)
        else:
            self._create(batch=batch)

    def _create(self, batch=None, remove_ex_search_items=False):
        self.validate()
        search_items_add, search_items_rm = self._search_items()
        rel_items_add, rel_items_rm = self._relation_items()

        items_add = search_items_add + rel_items_add
        items_remove = search_items_rm + rel_items_rm

        self.__table__.create(self.__model__.data, batch=batch)
        if remove_ex_search_items:
            self.__table__.batch_update(items_add, batch=batch)
            self.__table__.batch_delete_items(items_remove, batch=batch)
        else:
            self.__table__.batch_create(items_add, batch=batch)

    def _update(self, old_item, new_item, batch=None):
        self.__model__.data = {**old_item, **self.__model__.data, **new_item}
        self.__model__.data[self.__model__.__primary_key__] = old_item[
            self.__model__.__primary_key__
        ]
        self.__model__.data[self.__model__.__secondary_key__] = old_item[
            self.__model__.__secondary_key__
        ]
        if not util_b.is_same_json(old_item, self.__model__.data):
            self._create(batch=batch, remove_ex_search_items=True)

    def delete_by_pk(self, pk, batch=None):
        """
        プライマリキーからアイテムを削除
        Args:
            pk: Primary key
            batch: BatchWriteItem
        """
        self.__table__.clear_item(pk, batch=batch)

    def delete(self, target: dict = None, batch=None):
        """
        辞書型からアイテムを削除
        Args:
            batch: BatchWriteItem
        """
        target = target or self.__model__.data
        if target.get(self.__model__.__unique_keys__[0]):
            # unique があれば unique で削除
            self.delete_by_unique(
                target[self.__model__.__unique_keys__[0]], batch=batch
            )
        elif target.get(self.__model__.__primary_key__):
            # pk があれば pk で削除
            self.delete_by_pk(target[self.__model__.__primary_key__], batch=batch)
        else:
            # 両方とも無ければエラー
            raise ValidationError("Primary key or Unique key is required.")

    def delete_by_unique(self, value, batch=None):
        """
        ユニークキーからアイテムを削除
        Args:
            batch: BatchWriteItem
        """
        target = self.get_by_unique(value)
        pk = target.get(self.__model__.__primary_key__)
        self.delete_by_pk(pk, batch=batch)

    def _relation_item(self, pk, field: DBField):
        """関連付け"""
        return {
            self.__model__.__primary_key__: self.__model__.data[
                self.__model__.__primary_key__
            ],
            self.__model__.__secondary_key__: self.__table__.rel_key(pk),
            self.__table__.__search_data_key__: field.name,
        }

    def _get_other_item_by_unique(
        self, target: BaseModel, value, table=None, default=None
    ):
        q = Query(table or self.__table__, target)
        res = q.get_by_unique(value)
        return res

    def _field2relation_items(self, field: DBField, value):
        if not value:
            # 空の場合は空リストを返す
            return []

        pks = []
        if not field.is_list():
            # リストでない場合はリストに変換
            value = [value]
        if field.reletion_by_unique:
            # Unique Key で関連付け
            rel: BaseModel = field.relation()
            for x in value:
                # Unique Key で関連アイテムを取得
                _rel_item = self._get_other_item_by_unique(rel, x, default={})
                if _rel_item:
                    pks.append(_rel_item.get(rel.__primary_key__))
                elif field.relation_raise_if_not_found:
                    # 存在しない場合はエラー
                    raise NotFoundError(f"{rel.__model_name__}={x}")
        else:
            # Primary key で関連付け
            for x in value:
                pk = self.get(pk=x)
                if pk:
                    # 存在するものだけ追加
                    pks.append(pk)
                elif field.relation_raise_if_not_found:
                    # 存在しない場合はエラー
                    raise NotFoundError(f"{self.__model__.__model_name__}={x}")
        # Primary key が None のものを除外して、関連アイテムを作成
        pks = [pk for pk in pks if pk is not None]
        result = [self._relation_item(pk, field) for pk in pks]
        return result

    def _relation_items(self):
        items_add = []
        items_exist = []
        for k in self.__model__.__relation_keys__:
            field: DBField = self.__model__.__class__.__dict__[k]
            rel: BaseModel = field.relation
            _items_exist = self.__table__.relation(
                self.__model__.data[self.__model__.__primary_key__], rel.__model_name__
            )
            _items_exist = [
                self._relation_item(i[self.__table__.__primary_key__], field)
                for i in _items_exist
            ]
            if k in self.__model__.data.keys():
                _items_add = self._field2relation_items(field, self.__model__.data[k])
                items_add.extend(_items_add)
            items_exist.extend(_items_exist)
        sk_add = [item[self.__model__.__secondary_key__] for item in items_add]
        sk_exist = [item[self.__model__.__secondary_key__] for item in items_exist]
        # 削除 .. 既存のリストから追加リストを引く
        items_remove = [
            i for i in items_exist if i[self.__model__.__secondary_key__] not in sk_add
        ]
        # 追加 .. 追加リストから既存のリストを引く
        items_add = [
            i for i in items_add if i[self.__model__.__secondary_key__] not in sk_exist
        ]
        return items_add, items_remove

    def get_relation(self, model: BaseModel = "", field: DBField = "", pk_only=False):
        # 関連を検索
        if not isinstance(model or "", str):
            model = model.__model_name__
        if not isinstance(field or "", str):
            field = field.name
        return self.__table__.relation(
            self.__model__.data[self.__model__.__primary_key__],
            model_name=model,
            field_name=field,
            pk_only=pk_only,
        )

    def get_reference(self, model: BaseModel = "", field: DBField = "", pk_only=False):
        # 参照を検索
        if not isinstance(model or "", str):
            model = model.__model_name__
        if not isinstance(field or "", str):
            field = field.name
        return self.__table__.reference(
            self.__model__.data[self.__model__.__primary_key__],
            model_name=model,
            field_name=field,
            pk_only=pk_only,
        )
