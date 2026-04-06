# Imports and registers routes on shared resolver - orders_routes.py
from myapp.shared_resolver import app  # type: ignore[import-not-found]


@app.get("/orders")
def get_orders():
    return []
