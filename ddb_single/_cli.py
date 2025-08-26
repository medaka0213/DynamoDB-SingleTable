import importlib
import inspect
from typing import Dict, Type

import click

from ddb_single.model import BaseModel
from ddb_single.query import Query
from ddb_single.table import Table


def apply_model_change_records(module_path: str) -> None:
    """Regenerate search records for all table items to reflect model changes.

    Args:
        module_path (str): Python module path that defines a :class:`Table` instance
            named ``table`` and the corresponding :class:`BaseModel` classes.
    """
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        # モジュールが見つからなかった場合はエラー
        raise ValueError("module not found") from exc

    table = getattr(module, "table", None)
    if not isinstance(table, Table):
        # テーブルが見つからなかった場合はエラー
        raise ValueError("table instance not found in module")

    models: Dict[str, Type[BaseModel]] = {}
    for obj in module.__dict__.values():
        if inspect.isclass(obj) and issubclass(obj, BaseModel):
            # 同じテーブルに属するモデルのみ収集
            if getattr(obj, "__table__", None) == table:
                models[obj.__model_name__] = obj

    for item in table.all_items():
        model_name = table.pk2model(item[table.__primary_key__])
        model_cls = models.get(model_name)
        if model_cls is None:
            # 対応するモデルが存在しない場合はスキップ
            continue
        model = model_cls(__skip_validation__=True, **item)
        query = Query(table, model)
        add_items, rm_items = query._search_items()
        if add_items:
            # 足りない検索レコードを追加
            table.batch_create(add_items)
        if rm_items:
            # 不要な検索レコードを削除
            table.batch_delete_items(rm_items)


@click.group()
def cli() -> None:
    """Command line interface for DynamoDB SingleTable."""


@cli.command("apply-model-change")
@click.argument("module")
def apply_model_change(module: str) -> None:
    """Rebuild search records for all items after model changes."""
    try:
        apply_model_change_records(module)
    except ValueError as exc:
        # エラーが発生した場合はCLIエラーとして出力
        raise click.ClickException(str(exc))


if __name__ == "__main__":
    cli()
