import requests
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.utilities.typing import LambdaContext

app = BedrockAgentResolver()


@app.post(
    "/todos",
    description="Creates a todo",
)
def create_todo(title: Annotated[str, Query(max_length=200, strict=True, description="The todo title")]) -> str:  # (1)!
    todo = requests.post("https://jsonplaceholder.typicode.com/todos", data={"title": title})
    todo.raise_for_status()

    return todo.json()["title"]


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
