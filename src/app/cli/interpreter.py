import datetime as dt
from typing import Any, Dict, List, Self, Type, Optional, Sequence
from collections import OrderedDict

from app.db.table import Row, Field, Table, TableFile, TableSchema
from app.db.runner import Database
from app.cli.parser import (
    QUERY_GRAMMAR,
    Command,
    ParseError,
    DeleteQuery,
    InsertQuery,
    SelectQuery,
    UpdateQuery,
    QueryVisitor,
    DropTableQuery,
    CreateTableQuery,
)
from app.db.datatypes import Int, Str, Bool, DType, DateTime


def dtype_to_value(value: DType) -> str:
    if isinstance(value, Int):
        return str(value.value)
    elif isinstance(value, Str):
        return f"'{value.value}'"
    elif isinstance(value, Bool):
        return str(value.value).lower()
    elif isinstance(value, DateTime):
        return f"{value.value.isoformat()}"
    else:
        raise ValueError(f"Unsupported value type: {type(value)}")


def value_to_dtype(value: str, dtype: Type[DType]) -> DType:
    if dtype is Int:
        return Int(value=int(value))
    elif dtype is Str:
        return Str(value=value)
    elif dtype is Bool:
        return Bool(value=bool(value))
    elif dtype is DateTime:
        return DateTime(value=dt.datetime.fromisoformat(value))
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")


def print_rows(rows: Sequence[Row], fields: Sequence[str]) -> None:
    printed_rows: list[tuple[str]] = []
    printed_rows.append(tuple(fields))
    for row in rows:
        printed_rows.append(
            tuple(dtype_to_value(row.values[field]) for field in fields)
        )

    col_widths = [max(len(str(x)) for x in col) for col in zip(*printed_rows)]
    for row in printed_rows:
        print(" | ".join(f"{x:<{col_widths[i]}}" for i, x in enumerate(row)))


class Executor:
    def __init__(self, db: Database):
        self.db = db

    def execute(self, command: Command) -> None:
        assert isinstance(command, Command)

        if isinstance(command, SelectQuery):
            self.select(command)
        elif isinstance(command, InsertQuery):
            self.insert(command)
        elif isinstance(command, UpdateQuery):
            self.update(command)
        elif isinstance(command, DeleteQuery):
            self.delete(command)
        elif isinstance(command, CreateTableQuery):
            self.create_table(command)
        elif isinstance(command, DropTableQuery):
            self.drop_table(command)
        else:
            raise ValueError(f"Unsupported command type: {type(command)}")

    def get_table(self, table_name: str) -> Optional[Table]:
        if table_name not in self.db.tables:
            return None
        return self.db.tables[table_name]

    def select(self, query: SelectQuery) -> None:
        table = self.get_table(query.table)
        if table is None:
            print(f"Table {query.table} does not exist!")
            return

        parsed_conditions = {
            k: value_to_dtype(v, table.schema.fields[k].datatype)
            for k, v in query.conditions.items()
        }
        results = table.select(parsed_conditions)
        print_rows(results, query.fields)

    def insert(self, query: InsertQuery) -> None:
        table = self.get_table(query.table)
        if table is None:
            print(f"Table {query.table} does not exist!")
            return

        query.values["id"] = Int(-1)  # always default to -1
        row = Row.from_raw_dict(
            schema=table.schema,
            values=query.values,
        )
        table.create(row)
        print_rows([row], list(table.schema.fields.keys()))

    def update(self, query: UpdateQuery) -> None:
        table = self.get_table(query.table)
        if table is None:
            print(f"Table {query.table} does not exist!")
            return

        if "id" in query.updates.keys():
            print(f"Field id is immutable!")
            return

        try:
            row = table.get(query.id)
        except ValueError:
            print(f"Row with id {query.id} does not exist!")
            return

        for field, value in query.updates.items():
            row.values[field] = value_to_dtype(
                value, table.schema.fields[field].datatype
            )

        updated_rows = table.update(row)
        noun = "entry" if updated_rows == 1 else "entries"
        print(f"Updated {updated_rows} {noun}!")

    def delete(self, query: DeleteQuery) -> None:
        table = self.get_table(query.table)
        if table is None:
            print(f"Table {query.table} does not exist!")
            return

        deleted_rows = table.delete(query.id)
        noun = "entry" if deleted_rows == 1 else "entries"
        print(f"{deleted_rows} {noun} deleted!")

    def create_table(self, query: CreateTableQuery) -> None:
        table = self.get_table(query.table)
        if table is not None:
            print(f"Table {query.table} already exists!")
            return
        fields = OrderedDict()
        for field in query.fields:
            fields[field.field] = Field(
                name=field.field,
                datatype=field.dtype,
                nullable=False,
            )
        schema = TableSchema(fields=fields)
        self.db.create_table(query.table, schema)
        print(f"Table {query.table} created!")

    def drop_table(self, query: DropTableQuery) -> None:
        table = self.get_table(query.table)
        if table is None:
            print(f"Table {query.table} does not exist!")
            return
        self.db.delete_table(query.table)
        print(f"Table {query.table} dropped!")


def repl(db: Database):
    print("Welcome to the Database REPL!")
    executor = Executor(db)
    while True:
        try:
            query = input(">>> ")
            tree = QUERY_GRAMMAR.parse(query)
            visitor = QueryVisitor()
            result = visitor.visit(tree)
            executor.execute(result)
        except ParseError as e:
            print(e)
            continue
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


def main():
    db = Database()
    repl(db)


if __name__ == "__main__":
    main()
