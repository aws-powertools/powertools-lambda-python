from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import content_types
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.exceptions import NotFoundError
from aws_lambda_powertools.logging import correlation_paths

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.not_found
@tracer.capture_method
def handle_not_found_errors(exc: NotFoundError) -> Response:
    # Return 418 upon 404 errors
    logger.info(f"Not found route: {app.current_event.path}")
    return Response(
        status_code=418,
        content_type=content_types.TEXT_PLAIN,
        body="I'm a teapot!",
    )


@app.get("/catch/me/if/you/can")
@tracer.capture_method
def catch_me_if_you_can():
    return {"message": "oh hey"}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
