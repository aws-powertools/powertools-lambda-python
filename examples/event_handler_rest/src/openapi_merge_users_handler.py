"""
Example: Users Lambda Handler (for OpenAPI Merge)

This is an example of a micro-function Lambda that would be discovered
by configure_openapi_merge.
"""

from __future__ import annotations

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver(enable_validation=True)


class User(BaseModel):
    id: int
    name: str
    email: str


@app.get("/users")
def get_users() -> list[User]:
    """Get all users."""
    return [
        User(id=1, name="John Doe", email="john@example.com"),
        User(id=2, name="Jane Doe", email="jane@example.com"),
    ]


@app.get("/users/<user_id>")
def get_user(user_id: int) -> User:
    """Get a specific user by ID."""
    return User(id=user_id, name="John Doe", email="john@example.com")


@app.post("/users")
def create_user(user: User) -> User:
    """Create a new user."""
    return user


def handler(event, context):
    return app.resolve(event, context)
