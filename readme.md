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

Each model has al least 3 keys
- primary_key ... Hash key for single item. default: `pk: {__model_name__}_{uuid}` 
- seconday_key ... Range key for item. default: `sk: {__model_name__}_item`
- unique_key ... key to identify the item is the same. Mainly used to update item.

And you can set `serch_key` to enable search via GSI 

```python
from ddb_single.model import BaseModel, DBField
from ddb_single.table import FieldType

class User(BaseModel):
    __table__=table
    __model_name__ = "user"
    name = DBField(unique_key=True)
    email = DBField(search_key=True)
    age = DBField(type=FieldType.NUMBER, search_key=True)
    description=DBField()
```

## Usage

need "Qurey" object for CRUD
- `query.model(foo).create`
- `query.model(foo).get`
- `query.model(foo).search`
- `query.model(foo).update`
- `query.model(foo).delete`

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

### Get single item

`get(pk)` to get single item.

```
user = query.model(User).get("user_xxxx")
print(user)
# -> {"pk":"user_xxxx", "sk":"user_item", "name":"John", "email":"john@example.com"}
```

`get_by_unique` to get item by `unique_key`

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

## Relationship

### Create Model

You can sat relationns to other models
`relation=BaseModel` to set relation.

```python
class BlogPost(BaseModel):
    __model_name__ = "blogpost"
    __table__=table
    name = DBField(unique_key=True)
    content = DBField()
    author = DBField(reletion=User)
```

### Create Item


```python
blogpost = BlogPost(
    title="Hello",
    content="Hello world",
    author=self.user
)
query.model(blogpost).create()
```

Then, tha value "reletion item" added

|pk|sk|data|name|title|author|content|
|-|-|-|-|-|-|-|
|user_xxxx|user_item||John|||
|user_xxxx|search_user_name|John|
|blogpost_xxxx|blogpost_item|||Hello|John|Hello world|
|blogpost_xxxx|search_blogpost_title|Hello|
|blogpost_xxxx|rel_user_xxxx|author|

In addition to main item (sk=`blogpost_item`), relation item (sk=`rel_{primary_key}`) added to table. The GSI `DataSearchIndex` is used to get "relation items" to extract target's pk.
Then, `batch_get` items by pk.

|sk = hash|data = range|pk|
|-|-|-|
|rel_user_xxxx|author|blogpost_xxxx|

### Search Relations

`get_relation(model=Basemodel)` to search relations

```python
blogpost = query.model(BlogPost).get_by_unique("Hello")
blogpost = BlogPost(**blogpost)

user = query.model(blogpost).get_relation(model=User)
print(user)
# -> [{"pk":"user_xxxx", "sk":"user_item", "name":"John"}]
```

Also `get_relation(field=DBField)` to specify field

```python
user = query.model(blogpost).get_relation(field=BlogPost.author)
print(user)
# -> [{"pk":"user_xxxx", "sk":"user_item", "name":"John"}]
```

### Search Reference

In this library, "reference" is antonym to relation

`get_reference(model=Basemodel)` to search items related to the item

```python
user = query.model(User).get_by_unique("John")
user = User(**blogpost)

blogpost = query.model(blogpost).get_reference(model=BlogPost)
print(blogpost)
# -> [{"pk":"blogpost_xxxx", "sk":"blogpost_item", "name":"Hello"}]
```

Also `get_reference(field=DBField)` to specify field

```python
blogpost = query.model(user).get_reference(field=BlogPost.author)
print(blogpost)
# -> [{"pk":"blogpost_xxxx", "sk":"blogpost_item", "name":"Hello"}]
```

### Update Relation

If relation key's value changed, relationship also changed.


```python
new_user = User(name="Michael")
blogpost = query.model(BlogPost).get_by_unique("Hello")
blogpost["author"] = new_user
blogpost = BlogPost(**blogpost)

query.model(blogpost).update()
```

Then, "reletion item" changed

|pk|sk|data|name|title|author|content|
|-|-|-|-|-|-|-|
|user_xxxx|user_item||John|||
|user_xxxx|search_user_name|John|
|user_yyyy|user_item||Michael|||
|user_yyyy|search_user_name|Michael|
|blogpost_xxxx|blogpost_item|||Hello|Michael|Hello world|
|blogpost_xxxx|search_blogpost_title|Hello|
|blogpost_xxxx|rel_user_yyyy|author|

### Delete Relation

If related item deleted, relationship also deleted

```python
query.model(user).delete_by_unique("Michael")
```

Then, "reletion item" deleted.
But main item's value is not chenged.

|pk|sk|data|name|title|author|content|
|-|-|-|-|-|-|-|
|user_xxxx|user_item||John|||
|user_xxxx|search_user_name|John|
|blogpost_xxxx|blogpost_item|||Hello|Michael|Hello world|
|blogpost_xxxx|search_blogpost_title|Hello|
