import abc
import struct
import datetime
import dataclasses
from typing import Any, List, Type, Union, Generic, TypeVar, ClassVar

T = TypeVar("T", int, str, datetime.datetime, bool, bytes, float)


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


class Real(DataType[float]):
    value: float

    def __init__(self, value: float) -> None:
        super().__init__(value)

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Real":
        return cls(value=struct.unpack(">d", raw)[0])

    def to_bytes(self) -> bytes:
        return struct.pack(">d", self.value)


class Str(DataType[str]):
    value: str

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Str":
        return cls(value=raw.decode("utf-8"))

    def to_bytes(self) -> bytes:
        return self.value.encode("utf-8")


class Char(DataType[str]):
    value: str

    def __new__(cls, value: str) -> "Char":
        if len(value) > 1:
            raise ValueError(f"Char value must be a single character, got {value}")
        return super().__new__(cls, value[0])

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Char":
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


class Picture(DataType[bytes]):
    value: bytes

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Picture":
        return cls(value=raw)

    def to_bytes(self) -> bytes:
        return self.value


DType = Union[Int, Real, Str, Char, Bool, DateTime, Picture]


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
