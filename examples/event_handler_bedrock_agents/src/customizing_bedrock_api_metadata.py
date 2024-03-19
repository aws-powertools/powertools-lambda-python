import requests

from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.models import Contact, Server
from aws_lambda_powertools.utilities.typing import LambdaContext

app = BedrockAgentResolver()


@app.get("/todos/<todo_id>", description="Gets a todo title by ID")
def get_todo_title(todo_id: int) -> str:
    todo = requests.get(f"https://jsonplaceholder.typicode.com/todos/{todo_id}")
    todo.raise_for_status()

    return todo.json()["title"]


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)


if __name__ == "__main__":
    print(
        app.get_openapi_json_schema(
            title="TODO's API",
            version="1.21.3",
            summary="API to manage TODOs",
            description="This API implements all the CRUD operations for the TODO app",
            tags=["todos"],
            servers=[Server(url="https://stg.example.org/orders", description="Staging server")],
            contact=Contact(name="John Smith", email="john@smith.com"),
        ),
    )
