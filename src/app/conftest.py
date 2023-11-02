import uuid
import asyncio
import logging
from typing import Any, Optional, AsyncGenerator

import pytest

from fastapi.testclient import TestClient

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
