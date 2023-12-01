from typing import Any, Dict, List, Type, Union, Optional

import pydantic

from app.db.table import TableSchema


class TableMeta(pydantic.BaseModel):
    name: str
    filename: str
    schema: TableSchema

    model_config = pydantic.ConfigDict(extra="ignore")


class Metadata(pydantic.BaseModel):
    tables: List[TableMeta] = pydantic.Field(default_factory=list)

    model_config = pydantic.ConfigDict(extra="ignore")
