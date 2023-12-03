import io
import abc
import logging
import os.path
import tempfile
from typing import Any, Dict, Type, Callable, Optional, Sequence, Generator
from pathlib import Path
from urllib.parse import urljoin

from pydantic import BaseModel, ValidationError, GetCoreSchemaHandler
from pydantic_core import core_schema
from pydantic_core.core_schema import ValidationInfo, str_schema, simple_ser_schema

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseStorage(abc.ABC):
    @abc.abstractmethod
    def exists(self, path: str) -> bool:
        ...

    @abc.abstractmethod
    def url(self, path: str, **kwargs: Any) -> str:
        ...

    @abc.abstractmethod
    def upload(self, file: io.BytesIO | bytes, filepath: str) -> "StorageFile":
        """Returns a filepath (usually the same filepath as given in params)"""
        ...

    @abc.abstractmethod
    def download(self, path: str) -> Optional[bytes]:
        ...

    @abc.abstractmethod
    def delete(self, path: str) -> bool:
        ...


class TmpStorage(BaseStorage):
    def __init__(self) -> None:
        self.root = tempfile.gettempdir()

    def _get_filepath(self, path: str) -> str:
        while path.startswith("/"):
            path = path[1:]
        return os.path.join(self.root, path)

    def exists(self, path: str) -> bool:
        filepath = self._get_filepath(path)
        return os.path.exists(filepath)

    def url(self, path: str, **kwargs: Any) -> str:
        # Dummy implementation
        return os.path.join("tmp-files", path)

    def upload(self, file: io.BytesIO | bytes, path: str) -> "StorageFile":
        if isinstance(file, bytes):
            file = io.BytesIO(file)

        filepath = self._get_filepath(path)
        Path("/".join(filepath.split("/")[:-1])).mkdir(parents=True, exist_ok=True)

        file.seek(0)
        chunk_size = 2048
        with open(filepath, "wb+") as f:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
        return StorageFile(path)

    def download(self, path: str) -> Optional[bytes]:
        filepath = self._get_filepath(path)
        if not os.path.exists(filepath):
            return None
        with open(filepath, "rb") as f:
            return f.read()

    def delete(self, path: str) -> bool:
        filepath = self._get_filepath(path)
        if not os.path.exists(filepath) or os.path.isdir(filepath):
            return False
        os.remove(filepath)
        return True


class LocalStorage(TmpStorage):
    def __init__(self, root: str, url_root: str) -> None:
        self.root = root
        self.url_root = url_root

    def _get_filepath(self, path: str) -> str:
        return os.path.join(self.root, path)

    def url(self, path: str, **kwargs: Any) -> str:
        return urljoin(self.url_root, path)


class StorageFile(str):
    """Stores a relative path to some file in the storage."""

    @classmethod
    def __get_validators__(cls) -> Generator[Callable[[Any], Any], None, None]:
        yield cls.validate

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: Type[Any],
        handler: Callable[[Any, ValidationInfo], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        python_schema = core_schema.general_plain_validator_function(cls.validate)
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=python_schema,
        )

    @classmethod
    def validate(cls, v: Any, info: ValidationInfo) -> "StorageFile":
        if not isinstance(v, str):
            raise TypeError("string required")
        return cls(v)

    def __repr__(self) -> str:
        return f"StorageFile({super().__repr__()})"

    def exists(self) -> bool:
        return storage.exists(self)

    def url(self) -> str:
        return storage.url(self)

    def download(self) -> Optional[bytes]:
        return storage.download(self)

    def delete(self) -> bool:
        return storage.delete(self)


storage: BaseStorage

match settings.STORAGE:
    case "tmp_filesystem":
        # Warning: tmp_filesystem is not meant to be a fully-featured storage.
        # Its purpose is to provide a dummy storage API for tests or unconfigured setups,
        # but not for a real-world environment.
        storage = TmpStorage()
    case "local":
        storage = LocalStorage(
            root=str(settings.MEDIA_PATH),
            url_root=urljoin(str(settings.ROOT_URL), settings.MEDIA_URL_PREFIX),
        )
    case s:
        raise ValueError(f"unsupported storage: {s}")
