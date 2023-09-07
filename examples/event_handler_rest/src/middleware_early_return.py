import middleware_global_middlewares_module
import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response

app = APIGatewayRestResolver()
logger = Logger()
app.use(
    middlewares=[
        middleware_global_middlewares_module.log_request_response,
        middleware_global_middlewares_module.enforce_correlation_id,  # (1)!
    ],
)


@app.get("/todos")
def get_todos():
    todos: Response = requests.get("https://jsonplaceholder.typicode.com/todos")  # (2)!
    todos.raise_for_status()

    # for brevity, we'll limit to the first 10 only
    return {"todos": todos.json()[:10]}


@logger.inject_lambda_context
def lambda_handler(event, context):
    return app.resolve(event, context)
