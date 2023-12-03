from typing import Any, Dict, Optional

from pydantic import model_validator

from .base import Settings as SettingsBase  # noqa  # fmt: skip


class Settings(SettingsBase):
    @model_validator(mode="before")
    @classmethod
    def override_default_storage(cls, values: dict[str, Any]) -> dict[str, Any]:
        # Ensure that tests will not accidentally use a production media folder
        values["STORAGE"] = "tmp_filesystem"
        return values


settings = Settings()
