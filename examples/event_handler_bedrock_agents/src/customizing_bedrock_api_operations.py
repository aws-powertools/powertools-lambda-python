import requests
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Body, Query
from aws_lambda_powertools.utilities.typing import LambdaContext

app = BedrockAgentResolver()


@app.get(
    "/todos/<todo_id>",
    summary="Retrieves a TODO item, returning it's title",
    description="Loads a TODO item identified by the `todo_id`",
    response_description="The TODO title",
    responses={
        200: {"description": "TODO item found"},
        404: {
            "description": "TODO not found",
        },
    },
    tags=["todos"],
)
def get_todo_title(
    todo_id: Annotated[int, Query(description="The ID of the TODO item to get the title from")],
) -> Annotated[str, Body(description="The TODO title")]:
    todo = requests.get(f"https://jsonplaceholder.typicode.com/todos/{todo_id}")
    todo.raise_for_status()

    return todo.json()["title"]


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
