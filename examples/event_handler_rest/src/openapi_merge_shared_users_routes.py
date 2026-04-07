# Imports and registers routes on shared resolver - users_routes.py
from myapp.shared_resolver import app  # type: ignore[import-not-found]


@app.get("/users")
def get_users():
    return []


@app.get("/users/<user_id>")
def get_user(user_id: str):
    return {"id": user_id}
