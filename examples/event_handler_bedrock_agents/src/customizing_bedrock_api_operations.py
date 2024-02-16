import requests
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.utilities.typing import LambdaContext

app = BedrockAgentResolver()


@app.get(
    "/todos/<todo_id>",
    summary="Retrieves a todo item, returning it's title",
    description="Loads a todo item identified by the `todo_id`",
    response_description="The todo title",
    responses={
        200: {"description": "Todo item found"},
        404: {
            "description": "Item not found",
        },
    },
    tags=["Todos"],
)
def get_todo_title(todo_id: Annotated[int, Query(description="The ID of the todo item to get the title from")]) -> str:
    todo = requests.get(f"https://jsonplaceholder.typicode.com/todos/{todo_id}")
    todo.raise_for_status()

    return todo.json()["title"]


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
