import abc
import struct
import datetime
import dataclasses
from typing import Any, List, Type, Union, Generic, TypeVar, ClassVar

T = TypeVar("T", int, str, datetime.datetime, bool)


@dataclasses.dataclass
class DataType(abc.ABC, Generic[T]):
    """DataType is a container for a value of a specific type."""

    value: T

    @classmethod
    @abc.abstractmethod
    def from_bytes(cls: Type["DataType"], raw: bytes) -> "DataType":
        raise NotImplementedError

    @abc.abstractmethod
    def to_bytes(self) -> bytes:
        raise NotImplementedError

    def __str__(self) -> str:
        return str(self.value)


class Int(DataType[int]):
    value: int

    def __init__(self, value: int) -> None:
        super().__init__(value)

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Int":
        return cls(value=struct.unpack(">i", raw)[0])

    def to_bytes(self) -> bytes:
        return struct.pack(">i", self.value)


class Str(DataType[str]):
    value: str

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Str":
        return cls(value=raw.decode("utf-8"))

    def to_bytes(self) -> bytes:
        return self.value.encode("utf-8")


class DateTime(DataType[datetime.datetime]):
    value: datetime.datetime

    @classmethod
    def from_bytes(cls, raw: bytes) -> "DateTime":
        timestamp = struct.unpack(">q", raw)[0]
        return cls(value=datetime.datetime.fromtimestamp(timestamp))

    def to_bytes(self) -> bytes:
        timestamp = int(self.value.timestamp())
        return struct.pack(">q", timestamp)


class Bool(DataType[bool]):
    value: bool

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Bool":
        return cls(value=struct.unpack("?", raw)[0])

    def to_bytes(self) -> bytes:
        return struct.pack("?", self.value)


DType = Union[Int, Str, Bool, DateTime]


def serialize_dtype(dt: Type[DType]) -> str:
    return dt.__name__


def deserialize_dtype(name: str) -> Type[DType]:
    match name:
        case "Int":
            return Int
        case "Str":
            return Str
        case "Bool":
            return Bool
        case "DateTime":
            return DateTime
        case _:
            raise ValueError(f"unknown dtype: {name}")
