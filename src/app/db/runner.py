import json
import os.path
from typing import Optional

from app.core.config import settings

from .meta import Metadata, TableMeta


class Database:
    def __init__(self):
        self.data_root = settings.DB_DATA_PATH.absolute()
        self.metadata_path = self.data_root / "meta.json"
        self.metadata = self.read_metadata()

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


