import datetime as dt
from enum import Enum
from typing import List, Optional
from collections import OrderedDict

import pydantic

from app.db.table import Row, Field, Table, TableFile, TableSchema
from app.db.runner import Database
from app.core.config import settings
from app.db.datatypes import Int, Str, Bool, DType, DateTime
from app.core.storages import StorageFile

db = Database()


class Gender(str, Enum):
    FEMALE = "f"
    MALE = "m"


class Rat(pydantic.BaseModel):
    id: int = pydantic.Field(default=-1)
    created_at: dt.datetime = pydantic.Field(default_factory=dt.datetime.now)
    owner_id: int = pydantic.Field(default=-1)
    is_booked: bool = pydantic.Field(default=False)
    name: str
    age_months: int
    gender: Gender
    price: int
    phone: str
    description: str
    image: StorageFile = pydantic.Field(default=StorageFile(""))

    @classmethod
    def from_row(cls, row: Row) -> "Rat":
        return Rat.model_validate(row.to_raw_dict())

    def to_row(self) -> Row:
        return Row.from_raw_dict(RatTable.schema, self.model_dump(mode="python"))


def get_rats_table() -> Table:
    table = db.get_table("rats")
    if table is None:
        schema = TableSchema(
            fields=OrderedDict(
                [
                    ("id", Field(name="id", datatype=Int, nullable=False)),
                    (
                        "created_at",
                        Field(name="created_at", datatype=DateTime, nullable=False),
                    ),
                    ("owner_id", Field(name="owner_id", datatype=Int, nullable=False)),
                    (
                        "is_booked",
                        Field(name="is_booked", datatype=Bool, nullable=False),
                    ),
                    ("name", Field(name="name", datatype=Str, nullable=False)),
                    (
                        "age_months",
                        Field(name="age_months", datatype=Int, nullable=False),
                    ),
                    ("gender", Field(name="gender", datatype=Str, nullable=False)),
                    ("price", Field(name="price", datatype=Int, nullable=False)),
                    ("phone", Field(name="phone", datatype=Str, nullable=False)),
                    (
                        "description",
                        Field(name="description", datatype=Str, nullable=False),
                    ),
                    ("image", Field(name="image", datatype=Str, nullable=False)),
                ]
            )
        )
        table = db.create_table("rats", schema)

    return table


RatTable: Table = get_rats_table()
