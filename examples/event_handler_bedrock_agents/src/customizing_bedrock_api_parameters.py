import requests
from typing_extensions import Annotated

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Body, Query
from aws_lambda_powertools.utilities.typing import LambdaContext

app = BedrockAgentResolver()

logger = Logger()


@app.post(
    "/todos",
    description="Creates a TODO",
)
def create_todo(
    title: Annotated[str, Query(max_length=200, strict=True, description="The TODO title")],  # (1)!
) -> Annotated[bool, Body(description="Was the TODO created correctly?")]:
    todo = requests.post("https://jsonplaceholder.typicode.com/todos", data={"title": title})
    try:
        todo.raise_for_status()
        return True
    except Exception:
        logger.exception("Error creating TODO")
        return False


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
