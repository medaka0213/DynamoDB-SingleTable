"""Shared test helpers (issue #124).

Centralizes the DynamoDB Local endpoint and the dummy AWS credentials used by
the test suite so individual test modules never embed connection settings.
Every value can be overridden through an environment variable, but the
defaults always point at DynamoDB Local (never at real AWS).
"""

import datetime
import os

from ddb_single.table import Table

TEST_ENDPOINT_URL = os.environ.get("DDB_TEST_ENDPOINT_URL", "http://localhost:8000")
TEST_REGION_NAME = os.environ.get("DDB_TEST_REGION_NAME", "us-west-2")
TEST_AWS_ACCESS_KEY_ID = os.environ.get("DDB_TEST_AWS_ACCESS_KEY_ID", "fakeMyKeyId")
TEST_AWS_SECRET_ACCESS_KEY = os.environ.get("DDB_TEST_AWS_SECRET_ACCESS_KEY", "fakeSecretAccessKey")


def make_table(name_prefix, timestamp=True, **kwargs):
    """Build a ``Table`` bound to DynamoDB Local with dummy credentials.

    ``name_prefix`` gets a timestamp suffix by default so each test
    module/class works on its own independent table. Pass ``timestamp=False``
    for tests that never call ``init()`` and just need a fixed name.
    Extra keyword arguments are forwarded to ``Table``.
    """
    table_name = name_prefix
    if timestamp:
        table_name += datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    return Table(
        table_name=table_name,
        endpoint_url=TEST_ENDPOINT_URL,
        region_name=TEST_REGION_NAME,
        aws_access_key_id=TEST_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=TEST_AWS_SECRET_ACCESS_KEY,
        **kwargs,
    )
