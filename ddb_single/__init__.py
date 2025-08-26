try:
    from ddb_single.model import BaseModel, DBField  # noqa: F401
    from ddb_single.table import Table  # noqa: F401
    from ddb_single.query import Query, apply_model_change_records  # noqa: F401
except Exception:
    pass

__VERSION__ = "0.0.0"
