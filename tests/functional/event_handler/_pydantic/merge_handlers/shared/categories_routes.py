"""Categories routes - imports shared resolver and registers routes."""

from __future__ import annotations

from tests.functional.event_handler._pydantic.merge_handlers.shared.resolver import app


@app.get("/categories")
def get_categories() -> list[dict]:
    """Get all categories."""
    return []
