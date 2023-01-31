import requests
from requests import Response

from aws_lambda_powertools.event_handler import ALBResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = ALBResolver()


@app.post("/todo")
def create_todo():
    data: dict = app.current_event.json_body
    todo: Response = requests.post("https://jsonplaceholder.typicode.com/todos", data=data)

    # Returns the created todo object, with a HTTP 201 Created status
    return {"todo": todo.json()}, 201


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
