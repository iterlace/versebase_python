import os
from typing import Any, Dict, Literal, Optional, Sequence

import pydantic
from pydantic import HttpUrl, DirectoryPath, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config._helpers import update_workdir

# Update a workdir once at the first import of settings
update_workdir()


class Settings(BaseSettings):
    ENVIRONMENT: Optional[Literal["production", "testing", "development"]] = None

    SENTRY_DSN: Optional[HttpUrl] = None

    DB_DATA_PATH: DirectoryPath

    STORAGE: Literal["tmp_filesystem", "local"] = "local"
    MEDIA_PATH: DirectoryPath
    MEDIA_ROOT_URL: HttpUrl

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file="app/core/config/local.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def environment_can_be_blank(cls, v: Optional[str]) -> str:
        if not v:
            return "local"
        return v
