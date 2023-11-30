import enum
import datetime as dt
import dataclasses
from typing import Any, Dict, List, Self, Sequence

from parsimonious.nodes import Node, NodeVisitor
from parsimonious.grammar import Grammar
from parsimonious.exceptions import ParseError

QUERY_GRAMMAR = Grammar(
    """\
grammar = command+

command = select / update / delete

select = "SELECT" ws fields ws "FROM" ws table_name ws ("WHERE" ws conditions)?
update = "UPDATE" ws table_name ws "SET" ws updates ws "WHERE" ws "id" ws* "=" ws* int
delete = "DELETE FROM" ws table_name ws "WHERE" ws "id" ws* "=" ws* int

fields = field (ws? "," ws? field)*
field = ~"[a-zA-Z0-9_]+"

table_name = ~"[a-zA-Z0-9_]+"

conditions = condition (ws "AND" ws condition)*
condition = field ws "=" ws value

updates = update_set (ws? "," ws? update_set)*
update_set = field ws "=" ws value

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


@dataclasses.dataclass
class SelectQuery:
    table: str
    fields: List[str]
    conditions: List[Dict[str, Any]]


@dataclasses.dataclass
class UpdateQuery:
    table: str
    updates: Dict[str, Any]
    id: int


@dataclasses.dataclass
class DeleteQuery:
    table: str
    id: int


class QueryVisitor(NodeVisitor):
    def visit_grammar(self, node, visited_children):
        return visited_children[0]

    def visit_command(self, node, visited_children):
        return visited_children[0]

    def visit_select(self, node, visited_children) -> SelectQuery:
        _, _, fields, _, _, _, table_name, _, conditions = visited_children
        conditions = conditions[0][2]
        return SelectQuery(table=table_name, fields=fields, conditions=conditions)

    def visit_update(self, node, visited_children) -> UpdateQuery:
        _, _, table_name, _, _, _, updates, _, _, _, _, _, _, _, id_ = visited_children
        return UpdateQuery(table=table_name, updates=updates, id=id_)

    def visit_delete(self, node, visited_children) -> DeleteQuery:
        _, _, table_name, _, _, _, _, _, _, _, id_ = visited_children
        return DeleteQuery(table=table_name, id=id_)

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
