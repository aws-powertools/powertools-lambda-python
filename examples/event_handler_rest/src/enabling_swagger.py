from typing import List

import requests
from pydantic import BaseModel, Field

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(enable_validation=True)
app.enable_swagger(path="/swagger")  # (1)!


class Todo(BaseModel):
    userId: int
    id_: int = Field(alias="id")
    title: str
    completed: bool


@app.post("/todos")
def create_todo(todo: Todo) -> str:
    response = requests.post("https://jsonplaceholder.typicode.com/todos", json=todo.dict(by_alias=True))
    response.raise_for_status()

    return response.json()["id"]


@app.get("/todos")
def get_todos() -> List[Todo]:
    todo = requests.get("https://jsonplaceholder.typicode.com/todos")
    todo.raise_for_status()

    return todo.json()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
