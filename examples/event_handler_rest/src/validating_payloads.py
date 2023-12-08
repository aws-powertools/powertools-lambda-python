from typing import List, Optional

import requests
from pydantic import BaseModel, Field

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(enable_validation=True)  # (1)!


class Todo(BaseModel):  # (2)!
    userId: int
    id_: Optional[int] = Field(alias="id", default=None)
    title: str
    completed: bool


@app.post("/todos")
def create_todo(todo: Todo) -> str:  # (3)!
    response = requests.post("https://jsonplaceholder.typicode.com/todos", json=todo.dict(by_alias=True))
    response.raise_for_status()

    return response.json()["id"]  # (4)!


@app.get("/todos")
@tracer.capture_method
def get_todos() -> List[Todo]:
    todo = requests.get("https://jsonplaceholder.typicode.com/todos")
    todo.raise_for_status()

    return todo.json()  # (5)!


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
