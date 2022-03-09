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

tracer = Tracer()
logger = Logger()

app = APIGatewayRestResolver()


@app.get(rule="/bad-request-error")
def bad_request_error():
    # HTTP  400
    raise BadRequestError("Missing required parameter")


@app.get(rule="/unauthorized-error")
def unauthorized_error():
    # HTTP 401
    raise UnauthorizedError("Unauthorized")


@app.get(rule="/not-found-error")
def not_found_error():
    # HTTP 404
    raise NotFoundError


@app.get(rule="/internal-server-error")
def internal_server_error():
    # HTTP 500
    raise InternalServerError("Internal server error")


@app.get(rule="/service-error", cors=True)
def service_error():
    raise ServiceError(502, "Something went wrong!")
    # alternatively
    # from http import HTTPStatus
    # raise ServiceError(HTTPStatus.BAD_GATEWAY.value, "Something went wrong)


def handler(event, context):
    return app.resolve(event, context)
