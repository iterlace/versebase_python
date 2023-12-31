import os
import typing
from typing import Any, Dict, List, Type, Tuple, Optional
from collections import OrderedDict

import pydantic

from .index import TableIndex
from .datatypes import Int, DType, serialize_dtype, deserialize_dtype

# Constants
DELIMITER_SIZE = 8
FIELDS_DELIMITER = b"\xff\x00\xff\x00\xff\x00\xff\x00"
ROWS_DELIMITER = b"\x00\x7f\x00\xff\x00\x7f\x00\xff"


# Custom Exceptions
class TableError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class FilePointerCorruptError(TableError):
    pass


class Field(pydantic.BaseModel):
    name: str
    datatype: Type[DType]
    nullable: bool = False

    def __init__(
        self, name: str, datatype: Type[DType], nullable: bool = False, **kwargs
    ) -> None:
        super().__init__(name=name, datatype=datatype, nullable=nullable, **kwargs)

    @pydantic.field_serializer("datatype")
    def serialize_dt(self, dt: Type[DType], _info: Any) -> str:
        return serialize_dtype(dt)

    @pydantic.field_validator("datatype", mode="before")
    @classmethod
    def deserialize_dt(cls, dt: str | Type[DType]) -> Type[DType]:
        if isinstance(dt, str):
            return deserialize_dtype(dt)

        return dt


class TableSchema(pydantic.BaseModel):
    fields: OrderedDict[str, Field]

    @pydantic.field_validator("fields")
    @classmethod
    def validate_fields(cls, v: OrderedDict[str, Field]) -> dict[str, Field]:
        if len(v) == 0:
            raise ValueError("TableSchema must have at least one field")
        for k, field in v.items():
            if k == "id" and field.name == "id":
                if field.datatype is Int:
                    break
        else:
            raise ValueError("TableSchema must have an 'id' field of dtype Int")
        return v

    def __str__(self):
        fields = ", ".join(
            [f"{f.name}: {f.datatype.__name__}" for f in self.fields.values()]
        )
        return f"TableSchema({fields})"


class Row:
    __slots__ = ["schema", "values"]

    def __init__(self, schema: TableSchema, values: tuple[DType, ...]):
        self.schema = schema
        self.values: OrderedDict[str, DType] = OrderedDict(
            zip(schema.fields.keys(), values)
        )

    def to_dict(self) -> dict[str, DType]:
        return {k: v for k, v in self.values.items()}

    def to_raw_dict(self) -> dict[str, Any]:
        return {k: v.value for k, v in self.values.items()}

    @classmethod
    def from_dict(cls, schema: TableSchema, values: dict[str, DType]) -> "Row":
        values_list: list[DType] = []
        for field in schema.fields.values():
            if field.name not in values:
                if field.nullable:
                    values_list.append(None)
                else:
                    raise ValueError(f"You must specify a value for {field}!")
            elif values[field.name] is None:
                if not field.nullable:
                    raise ValueError(f"Passed None to non-nullable field {field}!")
                values_list.append(None)
            else:
                values_list.append(values[field.name])
        return cls(schema, tuple(values_list))

    @classmethod
    def from_raw_dict(cls, schema: TableSchema, values: dict[str, Any]) -> "Row":
        parsed_values = {}
        for field_name, field_data in values.items():
            field = schema.fields[field_name]
            parsed_values[field_name] = field.datatype(field_data)

        return cls.from_dict(schema, parsed_values)

    @classmethod
    def from_bytes(cls, schema: TableSchema, raw: list[bytes]) -> "Row":
        values = []
        for field_name, field_data in zip(schema.fields.keys(), raw):
            field = schema.fields[field_name]
            values.append(field.datatype.from_bytes(field_data))
        return cls(schema, tuple(values))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Row):
            return NotImplemented

        if self.schema != other.schema:
            return False

        return all(
            self_value == other_value
            for self_value, other_value in zip(
                self.values.values(), other.values.values()
            )
        )


class TableFile:
    def __init__(self, filepath: str, schema: TableSchema):
        self.filepath = filepath
        self.schema = schema
        self.file = self.init_file(filepath)
        self.is_closed = False

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        self.is_closed = True
        self.file.close()

    @staticmethod
    def init_file(path: str) -> typing.BinaryIO:
        return open(path, "a+b", buffering=0)

    def seek(self, pos: int) -> None:
        assert not self.is_closed

        if pos >= 0:
            self.file.seek(pos, os.SEEK_SET)
        else:
            try:
                self.file.seek(pos + 1, os.SEEK_END)
            except OSError:
                raise ValueError("Tried to access negative position")

    def position(self) -> int:
        assert not self.is_closed

        return self.file.tell()

    def at_beginning(self) -> bool:
        assert not self.is_closed

        return self.position() == 0

    def at_end(self) -> bool:
        assert not self.is_closed

        current_pos = self.position()
        self.file.seek(0, os.SEEK_END)
        end_pos = self.position()
        self.file.seek(current_pos)
        return current_pos == end_pos

    def read_row(self) -> Optional[Tuple[Row, int, int]]:
        assert not self.is_closed

        if self.at_end():
            return None

        pos_begin = self.position()
        if not self.at_beginning() and not self.at_end():
            self.seek(pos_begin - DELIMITER_SIZE)
            read_delimiter = self.file.read(DELIMITER_SIZE)
            if read_delimiter != ROWS_DELIMITER:
                raise FilePointerCorruptError("File pointer is corrupt")

        buf = bytearray()
        fields_raw = []

        while not self.at_end():
            b = self.file.read(1)
            buf += b

            if len(buf) >= DELIMITER_SIZE:
                possible_delimiter = buf[-DELIMITER_SIZE:]

                at_row_end = possible_delimiter == ROWS_DELIMITER
                at_field_end = possible_delimiter == FIELDS_DELIMITER

                if at_row_end or at_field_end:
                    field = bytes(buf[:-DELIMITER_SIZE])
                    fields_raw.append(field)
                    buf.clear()

                if at_row_end:
                    break

        assert len(fields_raw) == len(self.schema.fields.keys())

        pos_end = self.position()
        return Row.from_bytes(self.schema, fields_raw), pos_begin, pos_end

    def write_row(self, row: Row) -> Tuple[int, int]:
        assert not self.is_closed

        self.seek(-1)

        begin_pos = self.position()
        for i, field_data in enumerate(row.values.values()):
            self.file.write(field_data.to_bytes())
            if i != len(row.schema.fields) - 1:
                self.file.write(FIELDS_DELIMITER)
        self.file.write(ROWS_DELIMITER)

        end_pos = self.position()
        self.file.flush()

        return begin_pos, end_pos

    def erase(self, begin: int, end: int) -> None:
        assert not self.is_closed

        if begin >= end:
            raise ValueError("Begin position must be less than end position")

        self.file.seek(end)
        data = self.file.read()
        self.file.truncate(begin)
        self.file.seek(begin)
        self.file.write(data)
        self.file.flush()


class Table:
    def __init__(self, name: str, filepath: str, schema: TableSchema):
        self.name = name
        self.file = TableFile(filepath, schema)
        self.index = TableIndex(filepath + ".idx")
        self.schema = schema

    def get(self, id_: int) -> Row:
        pos = self.index.get(id_)
        if pos is None:
            raise ValueError(f"Row with id {id_} does not exist")
        self.file.seek(pos)
        row = self.file.read_row()
        if row is None:
            raise ValueError(f"Row with id {id_} does not exist")
        return row[0]

    def select(self, filter_: Optional[Dict[str, DType]] = None) -> List[Row]:
        if filter_ is None:
            filter_ = {}

        rows = []
        self.file.seek(0)
        while not self.file.at_end():
            row_ = self.file.read_row()
            if row_ is None:
                break
            row: Row = row_[0]

            for k, v in filter_.items():
                if row.values[k] != v:
                    break
            else:
                rows.append(row)

        rows.sort(key=lambda row: row.values["id"].value)  # low-performant? yes it is.
        return rows

    def create(self, row: Row) -> int:
        row.values["id"] = Int(self.index.get_next_id())

        begin, end = self.file.write_row(row)
        self.index.set(row.values["id"].value, begin)
        return row.values["id"].value

    def update(self, row: Row) -> int:
        deleted = self.delete(row.values["id"].value)
        if deleted == 0:
            return 0
        self.file.seek(-1)

        begin, end = self.file.write_row(row)
        self.index.set(row.values["id"].value, begin)
        return 1

    def delete(self, id_: int) -> int:
        if (r := self.find(id_)) is None:
            return 0
        else:
            row, begin, end = r

        self.file.erase(begin, end)
        self.refresh_indexes()
        return 1

    def find(self, id_: int) -> Optional[Tuple[Row, int, int]]:
        self.file.seek(0)
        while not self.file.at_end():
            row_ = self.file.read_row()
            if row_ is None:
                break
            row, begin, end = row_
            if row.values["id"].value == id_:
                return row, begin, end
        return None

    def refresh_indexes(self) -> None:
        self.index.clear()
        self.file.seek(0)
        while not self.file.at_end():
            row_ = self.file.read_row()
            if row_ is None:
                break
            row, begin, end = row_
            self.index.set(row.values["id"].value, begin)

    @classmethod
    def schema_info(cls):
        pass
