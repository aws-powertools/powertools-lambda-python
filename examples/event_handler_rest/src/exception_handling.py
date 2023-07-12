import requests

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
    Response,
    content_types,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.exception_handler(ValueError)
def handle_invalid_limit_qs(ex: ValueError):  # receives exception raised
    metadata = {"path": app.current_event.path, "query_strings": app.current_event.query_string_parameters}
    logger.error(f"Malformed request: {ex}", extra=metadata)

    return Response(
        status_code=400,
        content_type=content_types.TEXT_PLAIN,
        body="Invalid request parameters.",
    )


@app.get("/todos")
@tracer.capture_method
def get_todos():
    # educational purpose only: we should receive a `ValueError`
    # if a query string value for `limit` cannot be coerced to int
    max_results: int = int(app.current_event.get_query_string_value(name="limit", default_value=0))

    todos: requests.Response = requests.get(f"https://jsonplaceholder.typicode.com/todos?limit={max_results}")
    todos.raise_for_status()

    return {"todos": todos.json()}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
