import requests

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver(enable_validation=True)


@app.get(
    "/todos/<todo_id>",
    summary="Retrieves a todo item",
    description="Loads a todo item identified by the `todo_id`",
    response_description="The todo object",
    responses={
        200: {"description": "Todo item found"},
        404: {
            "description": "Item not found",
        },
    },
    tags=["Todos"],
)
def get_todo_title(todo_id: int) -> str:
    todo = requests.get(f"https://jsonplaceholder.typicode.com/todos/{todo_id}")
    todo.raise_for_status()

    return todo.json()["title"]


@app.post(
    "/todos",
    summary="Creates a new todo item",
    description="Creates a new todo item and returns it",
    response_description="The created todo object",
    status_code=201,
    tags=["Todos"],
)
def create_todo(title: str) -> dict:
    return {"id": 1, "title": title}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
