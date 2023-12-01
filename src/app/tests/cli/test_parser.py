import pytest

from app.cli.parser import (
    QUERY_GRAMMAR,
    ParseError,
    DeleteQuery,
    SelectQuery,
    UpdateQuery,
    QueryVisitor,
    DropTableQuery,
    FieldWithDType,
    CreateTableQuery,
)
from app.db.datatypes import Int, Str, Bool, DType, DateTime


def test_select_single_filter():
    query = "SELECT id FROM users WHERE name = 'Alice'"
    tree = QUERY_GRAMMAR.parse(query)
    visitor = QueryVisitor()
    result = visitor.visit(tree)
    assert isinstance(result, SelectQuery)
    assert result.table == "users"
    assert result.fields == ["id"]
    assert result.conditions == [{"name": "Alice"}]


def test_select_multiple_filters():
    query = "SELECT id, name FROM users WHERE id = 1 AND name = 'Alice'"
    tree = QUERY_GRAMMAR.parse(query)
    visitor = QueryVisitor()
    result = visitor.visit(tree)
    assert isinstance(result, SelectQuery)
    assert result.table == "users"
    assert result.fields == ["id", "name"]
    assert result.conditions == [{"id": 1}, {"name": "Alice"}]


def test_update_single_set():
    query = "UPDATE users SET id = 2 WHERE id = 1"
    tree = QUERY_GRAMMAR.parse(query)
    visitor = QueryVisitor()
    result = visitor.visit(tree)
    assert isinstance(result, UpdateQuery)
    assert result.table == "users"
    assert result.updates == {"id": 2}
    assert result.id == 1


def test_update_multiple_set():
    query = "UPDATE users SET id = 2, name = 'Bob', test = 'test' WHERE id = 1"
    tree = QUERY_GRAMMAR.parse(query)
    visitor = QueryVisitor()
    result = visitor.visit(tree)
    assert isinstance(result, UpdateQuery)
    assert result.table == "users"
    assert result.updates == {"id": 2, "name": "Bob", "test": "test"}
    assert result.id == 1


def test_delete_query_parsing():
    query = "DELETE FROM users WHERE id = 1"
    tree = QUERY_GRAMMAR.parse(query)
    visitor = QueryVisitor()
    result = visitor.visit(tree)
    assert isinstance(result, DeleteQuery)
    assert result.table == "users"
    assert result.id == 1


def test_create_table():
    query = "CREATE TABLE users (id: Int, name: Str, birthday: DateTime, is_gay: Bool)"
    tree = QUERY_GRAMMAR.parse(query)
    visitor = QueryVisitor()
    result = visitor.visit(tree)
    assert isinstance(result, CreateTableQuery)
    assert result.table == "users"
    assert result.fields == [
        FieldWithDType(field="id", dtype=Int),
        FieldWithDType(field="name", dtype=Str),
        FieldWithDType(field="birthday", dtype=DateTime),
        FieldWithDType(field="is_gay", dtype=Bool),
    ]


def test_drop_table():
    query = "DROP TABLE users"
    tree = QUERY_GRAMMAR.parse(query)
    visitor = QueryVisitor()
    result = visitor.visit(tree)
    assert isinstance(result, DropTableQuery)
    assert result.table == "users"


def test_invalid_query():
    query = "INVALID QUERY"
    with pytest.raises(ParseError):
        tree = QUERY_GRAMMAR.parse(query)
