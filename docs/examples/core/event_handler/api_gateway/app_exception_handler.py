from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, Response
from aws_lambda_powertools.logging import correlation_paths

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.exception_handler(ValueError)
def handle_value_error(ex: ValueError):
    metadata = {"path": app.current_event.path}
    logger.error(f"Malformed request: {ex}", extra=metadata)

    return Response(
        status_code=400,
        content_type=content_types.TEXT_PLAIN,
        body="Invalid request",
    )


@app.get("/hello")
@tracer.capture_method
def hello_name():
    name = app.current_event.get_query_string_value(name="name")
    if name is not None:
        raise ValueError("name query string must be present")
    return {"message": f"hello {name}"}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
