import datetime as dt
import dataclasses
from typing import Any, Dict, List, Self, Type, Union, Sequence

from parsimonious.nodes import Node, NodeVisitor
from parsimonious.grammar import Grammar
from parsimonious.exceptions import ParseError

from app.db.datatypes import Int, Str, Bool, DType, DateTime

QUERY_GRAMMAR = Grammar(
    """\
grammar = ws* command ws*

command = select / update / insert / delete / create_table / drop_table

select = "SELECT" ws+ fields ws+ "FROM" ws+ table_name (ws+ "WHERE" ws conditions)?
insert = "INSERT INTO" ws+ table_name ws+ updates
update = "UPDATE" ws+ table_name ws+ "SET" ws+ updates ws+ "WHERE" ws+ "id" ws* "=" ws* int
delete = "DELETE FROM" ws+ table_name ws+ "WHERE" ws+ "id" ws* "=" ws* int
create_table = "CREATE TABLE" ws+ table_name ws+ "(" ws* fields_with_dtypes ws* ")"
drop_table = "DROP TABLE" ws+ table_name

fields = field (ws* "," ws* field)*
field = ~"[a-zA-Z0-9_]+"

fields_with_dtypes = field_with_dtype (ws* "," ws* field_with_dtype)*
field_with_dtype = field ws* ":" ws* dtype

table_name = ~"[a-zA-Z0-9_]+"

conditions = condition (ws "AND" ws condition)*
condition = field ws "=" ws value

updates = update_set (ws* "," ws* update_set)*
update_set = field ws? "=" ws? value

dtype = "Int" / "Str" / "DateTime" / "Bool"

value = bool / int / str / datetime

bool = "true" / "false"
int = "-"? ~"[0-9]+"
str = "'" ~"[^']*" "'"
datetime = date "T" time

date = year ws "-" ws month ws "-" ws day
time = hour ws ":" ws minute ws ":" ws second

year = ~"[0-9]{4}"
month = ~"0[1-9]|1[0-2]"
day = ~"0[1-9]|[12][0-9]|3[01]"

hour = ~"[01][0-9]|2[0-3]"
minute = ~"[0-5][0-9]"
second = ~"[0-5][0-9]"

ws = ~"\s*"

"""
)


class Command:
    pass


@dataclasses.dataclass
class FieldWithDType:
    field: str
    dtype: Type[DType]

    def __str__(self):
        return f"{self.field}: {self.dtype}"


@dataclasses.dataclass
class CreateTableQuery(Command):
    table: str
    fields: List[FieldWithDType]


@dataclasses.dataclass
class DropTableQuery(Command):
    table: str


@dataclasses.dataclass
class SelectQuery(Command):
    table: str
    fields: List[str]
    conditions: Dict[str, Any]


@dataclasses.dataclass
class InsertQuery(Command):
    table: str
    values: Dict[str, Any]


@dataclasses.dataclass
class UpdateQuery(Command):
    table: str
    updates: Dict[str, Any]
    id: int


@dataclasses.dataclass
class DeleteQuery(Command):
    table: str
    id: int


class QueryVisitor(NodeVisitor):
    def visit_grammar(self, node, visited_children):
        return visited_children[1]

    def visit_command(self, node, visited_children):
        return visited_children[0]

    def visit_select(self, node, visited_children) -> SelectQuery:
        _, _, fields, _, _, _, table_name, raw_conditions = visited_children
        conditions = {}
        if isinstance(raw_conditions, list):
            conditions_list = raw_conditions[0][3]
            for cond in conditions_list:
                for k, v in cond.items():
                    if k in conditions:
                        raise ParseError(f"Duplicate condition for field {k}")
                    conditions[k] = v
        return SelectQuery(table=table_name, fields=fields, conditions=conditions)

    def visit_insert(self, node, visited_children) -> InsertQuery:
        _, _, table_name, _, updates = visited_children
        return InsertQuery(table=table_name, values=updates)

    def visit_update(self, node, visited_children) -> UpdateQuery:
        _, _, table_name, _, _, _, updates, _, _, _, _, _, _, _, id_ = visited_children
        return UpdateQuery(table=table_name, updates=updates, id=id_)

    def visit_delete(self, node, visited_children) -> DeleteQuery:
        _, _, table_name, _, _, _, _, _, _, _, id_ = visited_children
        return DeleteQuery(table=table_name, id=id_)

    def visit_create_table(self, node, visited_children) -> CreateTableQuery:
        _, _, table_name, _, _, _, fields, _, _ = visited_children
        return CreateTableQuery(table=table_name, fields=fields)

    def visit_drop_table(self, node, visited_children) -> DropTableQuery:
        _, _, table_name = visited_children
        return DropTableQuery(table=table_name)

    def visit_fields(self, node, visited_children):
        # Extract field names from visited children, ignoring commas and whitespace
        fields = []
        for child in visited_children:
            if isinstance(child, Node) and child.expr_name == "field":
                fields.append(child.text)
            if isinstance(child, list):
                fields.extend(self.visit_fields(None, child))
        return fields

    def visit_field(self, node, visited_children):
        return node

    def visit_fields_with_dtypes(self, node, visited_children) -> list[FieldWithDType]:
        fields: list[FieldWithDType] = []
        for child in visited_children:
            if isinstance(child, FieldWithDType):
                fields.append(child)
            if isinstance(child, list):
                fields.extend(self.visit_fields_with_dtypes(None, child))
        return fields

    def visit_field_with_dtype(self, node, visited_children) -> FieldWithDType:
        return FieldWithDType(field=visited_children[0].text, dtype=visited_children[4])

    def visit_dtype(self, node, visited_children) -> DType:
        return {
            "Int": Int,
            "Str": Str,
            "DateTime": DateTime,
            "Bool": Bool,
        }[node.text]

    def visit_table_name(self, node, visited_children):
        return node.text

    def visit_conditions(self, node, visited_children) -> List[Dict[str, Any]]:
        filters = [visited_children[0]]
        if len(visited_children) > 1:
            for v in visited_children[1]:
                filters.append(v[3])
        return filters

    def visit_condition(self, node, visited_children):
        field, _, _, _, value = visited_children
        return {field.text: value}

    def visit_updates(self, node, visited_children):
        updates = [visited_children[0]]
        if len(visited_children) > 1:
            for v in visited_children[1]:
                updates.append(v[3])
        return dict(updates)

    def visit_update_set(self, node, visited_children):
        field, _, _, _, value = visited_children
        return (field.text, value)

    def visit_value(self, node, visited_children):
        return visited_children[0]

    def visit_bool(self, node, visited_children):
        return node.text == "true"

    def visit_int(self, node, visited_children):
        return int(node.text)

    def visit_str(self, node, visited_children):
        return node.text.strip("'")

    def visit_datetime(self, node, visited_children) -> dt.datetime:
        return dt.datetime.fromisoformat(node.text)

    def visit_date(self, node, visited_children) -> str:
        return node.text

    def visit_time(self, node, visited_children) -> str:
        return node.text

    def generic_visit(self, node, visited_children):
        return visited_children or node
