import os

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(  # type: ignore[no-untyped-def]
    args,
    early_config,
    parser,
) -> None:
    os.environ["ENVIRONMENT"] = "testing"
