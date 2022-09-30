# DynamoDB SingleTable

Python DynamoDB interface, specialized in single-table design.
DynamoDB is high-performance serverless NoSQL, but difficult to disign tables.

Single-table design needs only single table, and few GSIs (Global Secondary Indexes).
It makes effective and easy to manage your whole data models for single service.

## Getting Started

### Init Table

```python
from ddb_single.table import Table
from ddb_single.query import Query

table = Table(
    table_name="sample",
    endpoint_url="http://localhost:8000",
)
table.init()
```

### Data Models

Each model hava to set 3 keys
- primary_key ... Hash key for single item. default: `{__model_name__}_{uuid}` 
- seconday_key ... Range key for item. default: `{__model_name__}_item`
- unique_key ... key to identify the item is the same. Mainly used to update item.

And you can set `serch_key` to enable search via GSI 

```python
from ddb_single.model import BaseModel, DBField
from ddb_single.table import FieldType

class User(BaseModel):
    __table__=table
    __model_name__ = "user"
    pk = DBField(primary_key=True)
    sk = DBField(secondary_key=True)
    name = DBField(unique_key=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description=DBField()
```

## Usage

need "Qurey" object for CRUD; `query.model(foo).create or search or update or delete`

```python
query = Query(table)
```


### Create Item

If the item with same value of `unique_key` already exist, exist item is updated.

```python
user = User(name="John", email="john@example.com", description="test")
query.model(user).create()
```

Then, multible items added.

|pk|sk|data|name|email|description|
|-|-|-|-|-|-|
|user_xxxx|user_item||John|john@example.com|test|
|user_xxxx|search_user_name|John|
|user_xxxx|search_user_email|new-john@example.com|

In addition to main item (sk=`user_item`), multiple item (sk=`search_{__model_name__}_{field_name}`) added to table.
Those "search items" are used to search

The GSI `DataSearchIndex` is used to get "search items" to extract target's pk.
Then, `batch_get` items by pk.

|sk = hash|data = range|pk|
|-|-|-|
|search_user_name|John|user_xxxx|
|search_user_email|new-john@example.com|user_xxxx|

### Search Items

```python
user = query.model(User).search(User.name.eq("John"))
print(user)
# -> [{"pk":"user_xxxx", "sk":"user_item", "name":"John", "email":"john@example.com"}]
```

`get_by_unique` is easy to get single item by `unique_key`

```python
user = query.model(User).get_by_unique("John")
print(user)
# -> {"pk":"user_xxxx", "sk":"user_item", "name":"John", "email":"john@example.com"}
```

### Update Item

```python
user = query.model(User).search(User.email.eq("john@example.com"))
new_user = User(**user[0])
new_user.email = "new-john@example.com"
query.model(new_user).update()
```

Or use unique value to detect exist item.

```python
new_user = User(name="John", email="new-john@example.com")
query.model(new_user).update()
```

Then, tha value of "main item" and "seach item" changed

|pk|sk|data|name|email|description|
|-|-|-|-|-|-|
|user_xxxx|user_item||John|new-john@example.com|test|
|user_xxxx|search_user_name|John|
|user_xxxx|search_user_email|new-john@example.com|


### Delete Item


```
user = query.model(User).search(User.email.eq("new-john@example.com"))
query.model(user[0]).delete()
```

Or use unique value to detect exist item.

```
query.model(User).delete_by_unique("John")
```



