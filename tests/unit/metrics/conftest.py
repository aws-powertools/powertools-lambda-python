from __future__ import annotations

import pytest


@pytest.fixture
def namespace() -> str:
    return "test_namespace"
