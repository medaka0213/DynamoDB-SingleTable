import importlib
import inspect

import click

from ddb_single.model import BaseModel
from ddb_single.query import apply_model_change_records
from ddb_single.table import Table


def _apply_model_change_records_from_path(module_path: str) -> None:
    """Regenerate search records for all table items to reflect model changes.

    This function loads models from a module path (legacy interface).
    For direct use with model classes, use apply_model_change_records() instead.

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

    models = []
    for obj in module.__dict__.values():
        if inspect.isclass(obj) and issubclass(obj, BaseModel):
            # 同じテーブルに属するモデルのみ収集
            if getattr(obj, "__table__", None) == table:
                models.append(obj)

    if not models:
        raise ValueError("no BaseModel classes found in module")

    # Use the new function
    apply_model_change_records(table, models)


@click.group()
def cli() -> None:
    """Command line interface for DynamoDB SingleTable."""


@cli.command("apply-model-change")
@click.argument("module")
def apply_model_change(module: str) -> None:
    """Rebuild search records for all items after model changes."""
    try:
        _apply_model_change_records_from_path(module)
    except ValueError as exc:
        # エラーが発生した場合はCLIエラーとして出力
        raise click.ClickException(str(exc))


if __name__ == "__main__":
    cli()
