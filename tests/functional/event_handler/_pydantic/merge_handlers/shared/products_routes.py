"""Products routes - imports shared resolver and registers routes."""

from __future__ import annotations

from tests.functional.event_handler._pydantic.merge_handlers.shared.resolver import app


@app.get("/products")
def get_products() -> list[dict]:
    """Get all products."""
    return []


@app.get("/products/<product_id>")
def get_product(product_id: str) -> dict:
    """Get a product by ID."""
    return {"id": product_id}
