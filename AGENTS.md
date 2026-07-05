# AGENTS.md

This file provides guidance to coding agents (Claude Code, Codex, etc.) when working
with code in this repository. `CLAUDE.md` is a symlink to this file.

## Development Commands

This project uses [uv](https://docs.astral.sh/uv/) for dependency management,
[ruff](https://docs.astral.sh/ruff/) for linting/formatting, and DynamoDB Local for tests.

### Environment Setup
```bash
# Install uv (see https://docs.astral.sh/uv/getting-started/installation/)
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (creates .venv and installs from uv.lock)
uv sync

# Start DynamoDB Local (required for tests)
docker compose up -d
# Or alternatively:
docker run -d --rm -p 8000:8000 amazon/dynamodb-local
```

If Docker is unavailable, DynamoDB Local can be started on the host with Java:
```bash
curl -O https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz
tar xzf dynamodb_local_latest.tar.gz
cd dynamodb_local
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
```
Either way, the endpoint is `http://localhost:8000`.

### Testing
```bash
# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest tests/test_query.py -v

# Run specific test
uv run pytest tests/test_query.py::TestCRUD::test_02_0_search -v

# Run with coverage
uv run pytest --cov=ddb_single tests/
```

### Linting & Formatting
```bash
# Lint (line-length=120, mccabe max-complexity=20)
uv run ruff check .

# Auto-fix lint issues
uv run ruff check --fix .

# Format
uv run ruff format .
```

### Documentation
```bash
# Build documentation (Sphinx)
cd docs_src && uv run make html
```

### Build & Publish
```bash
# Build sdist + wheel
uv build

# Bump version (major | minor | patch | stable | alpha | beta | rc)
uv version --bump patch

# Publish to PyPI (set UV_PUBLISH_TOKEN or pass --token)
uv publish
```

## Architecture Overview

This library implements a **Single-Table Design** pattern for DynamoDB, where multiple entity types are stored in one table using sophisticated key structures and Global Secondary Indexes (GSIs).

### Core Components

1. **Table** (`ddb_single/table.py`): Manages DynamoDB connections and table operations. Creates tables with predefined GSI schema for efficient querying across different data types.

2. **BaseModel** (`ddb_single/model.py`): Base class for data models. Models automatically discover fields, validate data, and handle relationships. Each model generates keys in the format:
   - Primary key: `{model_name}_{uuid}`
   - Secondary key: `{model_name}_item` (main), `search_{model_name}_{field}` (search), `rel_{pk}` (relations)

3. **DBField** (`ddb_single/model.py`): Field definition with type validation and query building. Key field types:
   - `unique_key=True`: Creates searchable unique constraint
   - `search_key=True`: Creates additional search items with dedicated GSI
   - `relation=ModelClass`: Establishes relationships between models

4. **Query** (`ddb_single/query.py`): CRUD operations and search interface. Important methods:
   - `_search_items()`: Creates/manages search items for indexed fields
   - `_relation_items()`: Manages relationship tracking items
   - Complex search with staged (GSI) and filter (scan) conditions

### Key Patterns

**Search Item Management**: When a model has `search_key=True` fields, the system creates separate items (`sk=search_{model}_{field}`) that are indexed by GSIs for efficient querying. The `_search_items()` method in Query handles this.

**Relationship Tracking**: Relations create bidirectional references using special items (`sk=rel_{pk}`). Forward relations use `get_relation()`, backward references use `get_reference()`.

**Query Expression Building**: DBField methods (eq, ne, lt, gt, between, contains) build `SearchExpression` objects that determine whether to use GSI (staged) or filter (scan) based on field type and operation.

### Critical Implementation Details

- **Field Value Assignment**: In `query.py:_search_items()`, always use `self.__model__.data.get(k)` for field values, not `field.value` (which is shared across instances).

- **GSI Structure**: Three GSIs for different data types:
  - `DataSearchIndex`: String fields
  - `DataSearchNumberIndex`: Number fields
  - `DataSearchBinaryIndex`: Binary fields

- **Batch Operations**: Use `batch=` parameter in create/update/delete for efficient bulk operations.

- **Case-Insensitive Search**: Fields with `ignore_case=True` store lowercase values in search items.

## Testing Approach

Tests use DynamoDB Local on port 8000. Each test class creates a unique table with timestamp to avoid conflicts. Test models should define `__table__` and `__model_name__` attributes.

Common test pattern:
```python
table = Table(
    table_name="test_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    endpoint_url="http://localhost:8000",
    region_name="us-west-2",
    aws_access_key_id="fakeMyKeyId",
    aws_secret_access_key="fakeSecretAccessKey",
)
table.init()
```

## Important Notes

- Python 3.10+ required
- Always run DynamoDB Local before tests
- The library abstracts single-table design complexity - understand key generation patterns before modifying
- Search items are automatically managed - don't manually create `sk=search_*` items
- Relations require at least one unique_key field on models
