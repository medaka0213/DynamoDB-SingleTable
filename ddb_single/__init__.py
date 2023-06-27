from ddb_single.model import BaseModel, DBField  # noqa: F401
from ddb_single.table import Table  # noqa: F401
from ddb_single.query import Query  # noqa: F401

import os

__version__ = (
    os.environ.get("RELEASE_VERSION", "").split("/")[-1].replace("v", "") or "0.0.0"
)
