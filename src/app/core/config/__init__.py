import os

__all__ = ["settings"]
__environment = os.environ.get("ENVIRONMENT", None)

if __environment == "production":
    from .production import settings  # noqa  # fmt: skip
elif __environment == "testing":
    from .testing import settings  # noqa  # fmt: skip
elif __environment == "development":
    from .development import settings  # noqa  # fmt: skip
else:
    from .production import settings  # noqa  # fmt: skip
