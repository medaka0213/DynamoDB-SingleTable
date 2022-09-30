DynamoDB SingleTable
====================

Python DynamoDB interface, specialized in single-table design. DynamoDB
is high-performance serverless NoSQL, but difficult to disign tables.

Single-table design needs only single table, and few GSIs (Global
Secondary Indexes). It makes effective and easy to manage your whole
data models for single service.

Getting Started
---------------

Init Table
~~~~~~~~~~

.. code:: python

   from ddb_single.table import Table
   from ddb_single.query import Query

   table = Table(
       table_name="sample",
       endpoint_url="http://localhost:8000",
   )
   table.init()

Data Models
~~~~~~~~~~~

Each model hava to set 3 keys - primary_key ¡Ä Hash key for single item.
default: ``{__model_name__}_{uuid}`` - seconday_key ¡Ä Range key for
item. default: ``{__model_name__}_item`` - unique_key ¡Ä key to identify
the item is the same. Mainly used to update item.

And you can set ``serch_key`` to enable search via GSI

.. code:: python

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

Usage
-----

need ¡ÈQurey¡É object for CRUD;
``query.model(foo).create or search or update or delete``

.. code:: python

   query = Query(table)

Create Item
~~~~~~~~~~~

If the item with same value of ``unique_key`` already exist, exist item
is updated.

.. code:: python

   user = User(name="John", email="john@example.com", description="test")
   query.model(user).create()

Then, multible items added.

+----------+----------+----------+------+----------+----------+
| pk       | sk       | data     | name | email    | des      |
|          |          |          |      |          | cription |
+==========+==========+==========+======+==========+==========+
| u        | u        |          | John | john@exa | test     |
| ser_xxxx | ser_item |          |      | mple.com |          |
+----------+----------+----------+------+----------+----------+
| u        | search_u | John     |      |          |          |
| ser_xxxx | ser_name |          |      |          |          |
+----------+----------+----------+------+----------+----------+
| u        | s        | new-     |      |          |          |
| ser_xxxx | earch_us | john@exa |      |          |          |
|          | er_email | mple.com |      |          |          |
+----------+----------+----------+------+----------+----------+

In addition to main item (sk=\ ``user_item``), multiple item
(sk=\ ``search_{__model_name__}_{field_name}``) added to table. Those
¡Èsearch items¡É are used to search

The GSI ``DataSearchIndex`` is used to get ¡Èsearch items¡É to extract
target¡Çs pk. Then, ``batch_get`` items by pk.

================= ==================== =========
sk = hash         data = range         pk
================= ==================== =========
search_user_name  John                 user_xxxx
search_user_email new-john@example.com user_xxxx
================= ==================== =========

Search Items
~~~~~~~~~~~~

.. code:: python

   user = query.model(Test).search(Test.name.eq("John"))
   print(user)
   # -> [{"pk":"user_xxxx", "sk":"user_item", "name":"John", "email":"john@example.com"}]

``get_by_unique`` is easy to get single item by ``unique_key``

.. code:: python

   user = query.model(Test).get_by_unique("John")
   print(user)
   # -> {"pk":"user_xxxx", "sk":"user_item", "name":"John", "email":"john@example.com"}

Update Item
~~~~~~~~~~~

.. code:: python

   user = query.model(Test).search(Test.email.eq("john@example.com"))
   new_user = Test(**user[0])
   new_user.email = "new-john@example.com"
   query.model(new_user).update()

Or use unique value to detect exist item.

.. code:: python

   new_user = Test(name="John", email="new-john@example.com")
   query.model(new_user).update()

Then, tha value of ¡Èmain item¡É and ¡Èseach item¡É changed

+----------+----------+----------+------+----------+----------+
| pk       | sk       | data     | name | email    | des      |
|          |          |          |      |          | cription |
+==========+==========+==========+======+==========+==========+
| u        | u        |          | John | new-     | test     |
| ser_xxxx | ser_item |          |      | john@exa |          |
|          |          |          |      | mple.com |          |
+----------+----------+----------+------+----------+----------+
| u        | search_u | John     |      |          |          |
| ser_xxxx | ser_name |          |      |          |          |
+----------+----------+----------+------+----------+----------+
| u        | s        | new-     |      |          |          |
| ser_xxxx | earch_us | john@exa |      |          |          |
|          | er_email | mple.com |      |          |          |
+----------+----------+----------+------+----------+----------+

Delete Item
~~~~~~~~~~~

::

   user = query.model(Test).search(Test.email.eq("new-john@example.com"))
   query.model(user[0]).delete()

Or use unique value to detect exist item.

::

   query.model(User).delete_by_unique("John")