import middleware_global_middlewares_module  # (1)!
import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response

app = APIGatewayRestResolver()
logger = Logger()

app.use(middlewares=[middleware_global_middlewares_module.log_request_response])  # (2)!


@app.get("/todos", middlewares=[middleware_global_middlewares_module.inject_correlation_id])
def get_todos():
    todos: Response = requests.get("https://jsonplaceholder.typicode.com/todos")
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos.json()[:10]}


@logger.inject_lambda_context
def lambda_handler(event, context):
    return app.resolve(event, context)
