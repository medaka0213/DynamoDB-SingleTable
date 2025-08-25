# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Start DynamoDB Local (required for tests)
docker-compose up -d
# Or alternatively:
docker run -d --rm -p 8000:8000 amazon/dynamodb-local

# Install dependencies (uses Poetry)
poetry install
```

### Testing
```bash
# Run all tests
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_query.py -v

# Run specific test
poetry run pytest tests/test_query.py::TestCRUD::test_02_0_search -v

# Run with coverage
poetry run pytest --cov=ddb_single tests/
```

### Linting
```bash
# Run flake8 (max-line-length=120, max-complexity=20)
poetry run flake8 ddb_single/
```

### Documentation
```bash
# Build documentation (Sphinx)
cd docs_src && poetry run make html
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