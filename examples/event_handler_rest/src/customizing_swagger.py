from __future__ import annotations

from typing import TYPE_CHECKING

import requests
from pydantic import BaseModel, EmailStr, Field

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver(enable_validation=True)
app.enable_swagger(path="/_swagger", swagger_base_url="https://cdn.example.com/path/to/assets/")


class Todo(BaseModel):
    userId: int
    id_: int = Field(alias="id")
    title: str
    completed: bool


@app.get("/todos")
def get_todos_by_email(email: EmailStr) -> list[Todo]:
    todos = requests.get(f"https://jsonplaceholder.typicode.com/todos?email={email}")
    todos.raise_for_status()

    return todos.json()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
