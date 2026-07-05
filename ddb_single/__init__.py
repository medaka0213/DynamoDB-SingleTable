import logging

logger = logging.getLogger(__name__)

try:
    from ddb_single.model import BaseModel, DBField  # noqa: F401
    from ddb_single.query import Query, apply_model_change_records  # noqa: F401
    from ddb_single.table import Table  # noqa: F401
except ImportError:
    # 依存パッケージが未インストールでも import 自体は成功させる。
    # ImportError 以外の例外は握り潰さず、そのまま送出する (#399)
    logger.error("ddb_single の依存パッケージが見つからないため、一部シンボルを公開できません", exc_info=True)

__VERSION__ = "0.0.0"
