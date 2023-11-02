from typing import Any, Dict, Optional

from pydantic import (
    MongoDsn,
    RedisDsn,
    FieldValidationInfo,
    field_validator,
    model_validator,
)

from .base import Settings as SettingsBase  # noqa  # fmt: skip


class Settings(SettingsBase):
    pass


settings = Settings()
