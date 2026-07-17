"""Regression tests for issue #117.

``begins_with`` matching on model-name prefixes must not collide between
models where one model name is a prefix of another
(e.g. "user" vs "user_admin", "note" vs "note_child").
"""

import logging
import unittest
import uuid

from ddb_single.model import BaseModel, DBField
from ddb_single.query import Query
from tests.conftest import make_table

logging.basicConfig(level=logging.INFO)

# uuid suffix in the prefix keeps uniqueness at least as strong as the
# original timestamp+uuid name; make_table appends the timestamp itself.
table = make_table(f"prefix_col_{uuid.uuid4().hex}_")
table.init()


class User(BaseModel):
    __table__ = table
    __model_name__ = "user"
    name = DBField(unique_key=True)


class UserAdmin(BaseModel):
    __table__ = table
    __model_name__ = "user_admin"
    name = DBField(unique_key=True)


class Note(BaseModel):
    __table__ = table
    __model_name__ = "note"
    title = DBField(unique_key=True)
    user = DBField(relation=User)
    admin = DBField(relation=UserAdmin)


class NoteChild(BaseModel):
    __table__ = table
    __model_name__ = "note_child"
    title = DBField(unique_key=True)
    user = DBField(relation=User)


query = Query(table)


class TestPrefixCollision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User(name="alice")
        query.model(cls.user).create()
        cls.admin = UserAdmin(name="bob")
        query.model(cls.admin).create()
        cls.note = Note(title="note1", user=cls.user, admin=cls.admin)
        query.model(cls.note).create()
        cls.note_child = NoteChild(title="child1", user=cls.user)
        query.model(cls.note_child).create()

    def test_01_relation_no_cross_match(self):
        """get_relation(model=User) must not return user_admin items"""
        res = query.model(self.note).get_relation(model=User)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "alice")
        self.assertEqual(table.pk2model(res[0]["pk"]), "user")

        res = query.model(self.note).get_relation(model=UserAdmin)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "bob")
        self.assertEqual(table.pk2model(res[0]["pk"]), "user_admin")

        # 引数なしの場合は両方返る
        res = query.model(self.note).get_relation()
        self.assertEqual(len(res), 2)

    def test_02_reference_no_cross_match(self):
        """get_reference(model=Note) must not return note_child items"""
        res = query.model(self.user).get_reference(model=Note)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "note1")
        self.assertEqual(table.pk2model(res[0]["pk"]), "note")

        res = query.model(self.user).get_reference(model=NoteChild)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "child1")
        self.assertEqual(table.pk2model(res[0]["pk"]), "note_child")

        # フィールド指定の参照検索も同様
        res = query.model(self.user).get_reference(model=Note, field=Note.user)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "note1")

        # 引数なしの場合は両方返る
        res = query.model(self.user).get_reference()
        self.assertEqual(len(res), 2)

    def test_03_clear_relation_no_cross_delete(self):
        """clear_relation(model_name="user") must not delete user_admin relations"""
        note = Note(title="note2", user=self.user, admin=self.admin)
        query.model(note).create()
        note_pk = note.data["pk"]

        table.clear_relation(note_pk, model_name="user")
        # user への関連は削除される
        res = query.model(note).get_relation(model=User)
        self.assertEqual(len(res), 0)
        # user_admin への関連は残る
        res = query.model(note).get_relation(model=UserAdmin)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "bob")

    def test_04_clear_reference_no_cross_delete(self):
        """clear_reference(model_name="note") must not delete note_child references"""
        user = User(name="carol")
        query.model(user).create()
        note = Note(title="note3", user=user)
        query.model(note).create()
        note_child = NoteChild(title="child3", user=user)
        query.model(note_child).create()
        user_pk = user.data["pk"]

        table.clear_reference(user_pk, model_name="note")
        # note からの参照は削除される
        res = query.model(user).get_reference(model=Note)
        self.assertEqual(len(res), 0)
        # note_child からの参照は残る
        res = query.model(user).get_reference(model=NoteChild)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "child3")


if __name__ == "__main__":
    unittest.main()
