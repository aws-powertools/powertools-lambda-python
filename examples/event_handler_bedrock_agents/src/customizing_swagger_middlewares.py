from typing import List

import requests
from pydantic import BaseModel, EmailStr, Field

from aws_lambda_powertools.event_handler import BedrockAgentResolver, Response
from aws_lambda_powertools.event_handler.middlewares import NextMiddleware
from aws_lambda_powertools.utilities.typing import LambdaContext

app = BedrockAgentResolver()


def swagger_middleware(app: BedrockAgentResolver, next_middleware: NextMiddleware) -> Response:
    is_authenticated = ...
    if not is_authenticated:
        return Response(status_code=400, body="Unauthorized")

    return next_middleware(app)


app.enable_swagger(middlewares=[swagger_middleware])


class Todo(BaseModel):
    userId: int
    id_: int = Field(alias="id")
    title: str
    completed: bool


@app.get("/todos", description="Finds all todos by email")
def get_todos_by_email(email: EmailStr) -> List[Todo]:
    todos = requests.get(f"https://jsonplaceholder.typicode.com/todos?email={email}")
    todos.raise_for_status()

    return todos.json()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
