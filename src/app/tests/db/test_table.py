import uuid
import os.path
from typing import Any, Generator

import pytest

from app.db.index import TableIndex
from app.db.table import Row, Field, Table, TableFile, TableSchema
from app.db.datatypes import Int, Str, DType


class TestTableFile:
    @pytest.fixture(scope="function")
    def filepath(self) -> Generator[str, None, None]:
        path = f"/tmp/{uuid.uuid4()}"

        yield path

        if os.path.isfile(path):
            os.remove(path)

    @pytest.fixture(scope="function")
    def schema(self) -> Generator[TableSchema, None, None]:
        schema = TableSchema(
            fields={
                "id": Field(name="id", datatype=Int, nullable=False),
                "name": Field(name="name", datatype=Str, nullable=False),
            }
        )
        yield schema

    @pytest.fixture(scope="function")
    def row(self, schema: TableSchema) -> Row:
        return Row.from_raw(
            schema,
            [
                schema.fields["id"].datatype(value=1).to_bytes(),  # type: ignore[arg-type]
                schema.fields["name"].datatype(value="Bob").to_bytes(),  # type: ignore[arg-type]
            ],
        )

    def test_write_row(self, filepath: str, schema: TableSchema, row: Row) -> None:
        table_file = TableFile(filepath, schema)
        assert table_file.file is not None
        table_file.write_row(row)
        table_file.seek(0)

        r = table_file.read_row()
        assert r is not None

        read_row, begin, end = r
        assert read_row == row

    def test_seek(self, filepath: str, schema: TableSchema, row: Row) -> None:
        table_file = TableFile(filepath, schema)

        table_file.seek(0)
        assert table_file.file.tell() == 0
        table_file.seek(-1)
        assert table_file.file.tell() == 0

        begin, end = table_file.write_row(row)

        assert table_file.file.tell() == end
        assert table_file.at_end()
        assert not table_file.at_beginning()

        table_file.seek(0)
        assert table_file.file.tell() == 0
        assert not table_file.at_end()
        assert table_file.at_beginning()

        table_file.seek(-1)
        assert table_file.file.tell() == end
        table_file.seek(-5)
        assert table_file.file.tell() == end - 4

    def test_erase(self, filepath: str, schema: TableSchema, row: Row) -> None:
        table_file = TableFile(filepath, schema)
        table_file.file.write(b"hello world, my dear")
        table_file.file.flush()
        table_file.erase(5, 11)
        table_file.file.seek(0)
        assert table_file.file.read() == b"hello, my dear"


class TestTable:
    @pytest.fixture(scope="function")
    def filepath(self) -> Generator[str, None, None]:
        path = f"/tmp/{uuid.uuid4()}"

        yield path

        if os.path.isfile(path):
            os.remove(path)

        if os.path.isfile(path + ".idx"):
            os.remove(path + ".idx")

    def test_table_initialization(self, filepath: str) -> None:
        schema = TableSchema({"id": Field("id", Int)})
        table = Table("test_table", filepath, schema)
        assert table.name == "test_table"
        assert isinstance(table.file, TableFile)
        assert isinstance(table.index, TableIndex)

    def test_get_row_non_existing(self, filepath, mocker):
        schema = TableSchema({"id": Field("id", Int)})
        table = Table("test_table", filepath, schema)
        with pytest.raises(ValueError):
            table.get(99)

    def test_create_and_get_row(self, filepath: str) -> None:
        schema = TableSchema({"id": Field("id", Int), "name": Field("name", Str)})
        table = Table("test_table", filepath, schema)
        idx = table.create(Row(schema, (Int(1), Str("Alice"))))
        assert idx >= 0
        retrieved_row = table.get(idx)
        assert retrieved_row.values["id"] == Int(idx)
        assert retrieved_row.values["name"] == Str("Alice")

    def test_select_rows_with_data(self, filepath: str) -> None:
        schema = TableSchema({"id": Field("id", Int), "name": Field("name", Str)})
        table = Table("test_table", filepath, schema)
        # Creating multiple rows
        table.create(Row(schema, (Int(-1), Str("Alice"))))
        table.create(Row(schema, (Int(-1), Str("Bob"))))
        table.create(Row(schema, (Int(-1), Str("Alice"))))
        # Selecting rows with a specific name
        selected_rows = table.select({"name": Str("Alice")})
        assert len(selected_rows) == 2
        for row in selected_rows:
            assert row.values["name"] == Str("Alice")

    def test_create_row(self, filepath: str) -> None:
        schema = TableSchema({"id": Field("id", Int), "name": Field("name", Str)})
        table = Table("test_table", filepath, schema)
        idx = table.create(Row(schema, (Int(-1), Str("Alice"))))
        assert idx >= 0
        retrieved_row = table.get(idx)
        assert retrieved_row.values["id"] == Int(idx)
        assert retrieved_row.values["name"] == Str("Alice")

    def test_update_row(self, filepath: str) -> None:
        schema = TableSchema({"id": Field("id", Int), "name": Field("name", Str)})
        table = Table("test_table", filepath, schema)
        idx = table.create(Row(schema, (Int(-1), Str("Alice"))))

        # Update the row - modify this line to match your method's signature
        updated_row_data = Row(schema, (Int(idx), Str("Bob")))
        table.update(updated_row_data)  # Adjust this call as needed

        updated_row = table.get(idx)
        assert updated_row.values["name"] == Str("Bob")

    def test_delete_row(self, filepath: str) -> None:
        schema = TableSchema({"id": Field("id", Int), "name": Field("name", Str)})
        table = Table("test_table", filepath, schema)
        idx = table.create(Row(schema, (Int(-1), Str("Alice"))))
        table.delete(idx)
        with pytest.raises(ValueError):
            table.get(idx)
