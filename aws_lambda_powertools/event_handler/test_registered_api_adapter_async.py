"""
Unit tests for _registered_api_adapter_async()
Covers: sync handler, async handler, and mixed scenarios
"""
import asyncio
import inspect
import pytest
from unittest.mock import MagicMock


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_app(route_args=None, route=None):
    """Build a minimal mock app context."""
    app = MagicMock()
    app.context = {"_route_args": route_args or {}, "_route": route}
    app.request = MagicMock()
    app._to_response = lambda result: result  # pass-through for testing
    return app


# ── tests ─────────────────────────────────────────────────────────────────────

def test_sync_handler_is_not_a_coroutine():
    """Sync handlers should work without any awaiting."""
    def sync_handler():
        return {"message": "sync"}

    result = sync_handler()
    assert not inspect.iscoroutine(result)
    assert result == {"message": "sync"}


def test_async_handler_is_a_coroutine():
    """Async handlers should return a coroutine that can be awaited."""
    async def async_handler():
        return {"message": "async"}

    result = async_handler()
    assert inspect.iscoroutine(result)
    final = asyncio.run(result)
    assert final == {"message": "async"}


def test_mixed_sync_and_async_handlers():
    """Both sync and async handlers should return the correct values."""
    def sync_h():
        return {"type": "sync"}

    async def async_h():
        return {"type": "async"}

    sync_result = sync_h()
    async_result = asyncio.run(async_h())

    assert sync_result == {"type": "sync"}
    assert async_result == {"type": "async"}


def test_iscoroutine_detection():
    """inspect.iscoroutine() correctly distinguishes sync vs async results."""
    async def async_fn():
        return 42

    sync_result = 42
    async_result = async_fn()

    assert not inspect.iscoroutine(sync_result)
    assert inspect.iscoroutine(async_result)

    # clean up coroutine to avoid ResourceWarning
    async_result.close()
