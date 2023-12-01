import json
import os.path
from typing import Optional

from sortedcontainers import SortedDict

from app.db.table import Table, TableSchema
from app.core.config import settings

from .meta import Metadata, TableMeta


class Database:
    def __init__(self):
        self.data_root = settings.DB_DATA_PATH.absolute()
        self.metadata_path = self.data_root / "meta.json"
        self.metadata = self.read_metadata()

        # state
        self.tables = SortedDict()

    def read_metadata(self):
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                return Metadata.model_validate_json(f.read())
        else:
            meta = Metadata()
            self.write_metadata(override=meta)
        return meta

    def write_metadata(self, override: Optional[Metadata] = None):
        meta = override or self.metadata
        with open(self.metadata_path, "w") as f:
            f.write(json.dumps(meta.model_dump(mode="json")))

    def init_tables(self) -> None:
        for table in self.metadata.tables:
            self.tables[table.name] = Table(
                name=table.name,
                filepath=os.path.join(self.data_root, table.filename),
                # We use the same TableSchema object for both Table and Metadata.
                # It is useful to keep them in sync with no effort.
                schema=table.schema,
            )

    def create_table(self, name: str, schema: TableSchema) -> Table:
        if name in self.tables.keys():
            raise ValueError(f"Table {name} already exists")

        schema = schema.model_copy()
        filename = f"table_{name}.dat"
        self.metadata.tables.append(
            TableMeta(name=name, filename=filename, schema=schema)
        )
        self.write_metadata()
        table = Table(
            name=name,
            filepath=os.path.join(self.data_root, filename),
            # We use the same TableSchema object for both Table and Metadata.
            # It is useful to keep them in sync with no effort.
            schema=schema,
        )
        self.tables[name] = table
        return table

    def delete_table(self, name: str) -> None:
        if name not in self.tables.keys():
            raise ValueError(f"Table {name} does not exist")
        table: Table = self.tables[name]

        # remove the table from app's state and metadata
        self.tables.pop(name)
        self.metadata.tables = [
            table for table in self.metadata.tables if table.name != name
        ]
        self.write_metadata()

        # close fd and delete the file
        table.file.close()
        os.remove(table.file.filepath)
