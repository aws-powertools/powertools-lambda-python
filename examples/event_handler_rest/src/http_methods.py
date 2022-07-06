import requests
from requests import Response

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.post("/todos")
@tracer.capture_method
def create_todo():
    todo_data: dict = app.current_event.json_body  # deserialize json str to dict
    todo: Response = requests.post("https://jsonplaceholder.typicode.com/todos", data=todo_data)
    todo.raise_for_status()

    return {"todo": todo.json()}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
