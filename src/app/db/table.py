import io
import os
import struct
import typing
import dataclasses
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Tuple, Union, Optional
from collections import OrderedDict

import pydantic

from .datatypes import DType

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


@dataclasses.dataclass
class Field:
    name: str
    datatype: Type[DType]
    nullable: bool = False


@dataclasses.dataclass
class TableSchema:
    fields: dict[str, Field]

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

    @classmethod
    def from_raw(cls, schema: TableSchema, raw: list[bytes]) -> "Row":
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

    @staticmethod
    def init_file(path: str) -> typing.BinaryIO:
        return open(path, "a+b", buffering=0)

    def seek(self, pos: int) -> None:
        if pos >= 0:
            self.file.seek(pos, os.SEEK_SET)
        else:
            try:
                self.file.seek(pos + 1, os.SEEK_END)
            except OSError:
                raise ValueError("Tried to access negative position")

    def position(self) -> int:
        return self.file.tell()

    def at_beginning(self) -> bool:
        return self.position() == 0

    def at_end(self) -> bool:
        current_pos = self.position()
        self.file.seek(0, os.SEEK_END)
        end_pos = self.position()
        self.file.seek(current_pos)
        return current_pos == end_pos

    def read_row(self) -> Optional[Tuple[Row, int, int]]:
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
        return Row.from_raw(self.schema, fields_raw), pos_begin, pos_end

    def write_row(self, row: Row) -> Tuple[int, int]:
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
        if begin >= end:
            raise ValueError("Begin position must be less than end position")

        self.file.seek(end)
        data = self.file.read()
        self.file.truncate(begin)
        self.file.seek(begin)
        self.file.write(data)
        self.file.flush()


class Table:
    def __init__(
        self,
        name: str,
        filepath: str,
        schema: TableSchema,
        index: Optional[Any] = None,
    ):
        self.name = name
        self.file = TableFile(filepath, schema)
        self.index = index

    def get(self, id_: int) -> Row:
        pass

    def select(self, filter_: Dict[str, Any]) -> List[Row]:
        pass

    def create(self, row: Row) -> int:
        pass

    def update(self, row: Row) -> None:
        pass

    def delete(self, id_: int) -> None:
        pass

    def find(self, id_: int) -> Optional[Tuple[Row, int, int]]:
        pass

    def refresh_indexes(self) -> None:
        pass

    @classmethod
    def schema_info(cls):
        pass
