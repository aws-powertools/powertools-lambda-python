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
    return [
        User(id=1, name="John", email="john@example.com"),
    ]


@app.post("/users")
def create_user(user: User) -> User:
    return user


def handler(event, context):
    return app.resolve(event, context)
