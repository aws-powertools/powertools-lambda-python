import requests
from requests import Response

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.exceptions import (
    BadRequestError,
    InternalServerError,
    NotFoundError,
    ServiceError,
    UnauthorizedError,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.get(rule="/bad-request-error")
def bad_request_error():
    raise BadRequestError("Missing required parameter")  # HTTP  400


@app.get(rule="/unauthorized-error")
def unauthorized_error():
    raise UnauthorizedError("Unauthorized")  # HTTP 401


@app.get(rule="/not-found-error")
def not_found_error():
    raise NotFoundError  # HTTP 404


@app.get(rule="/internal-server-error")
def internal_server_error():
    raise InternalServerError("Internal server error")  # HTTP 500


@app.get(rule="/service-error", cors=True)
def service_error():
    raise ServiceError(502, "Something went wrong!")


@app.get("/todos")
@tracer.capture_method
def get_todos():
    todos: Response = requests.get("https://jsonplaceholder.typicode.com/todos")
    todos.raise_for_status()

    return {"todos": todos.json()[:10]}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
