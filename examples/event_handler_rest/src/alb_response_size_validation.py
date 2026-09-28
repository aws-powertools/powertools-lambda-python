from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import ALBResolver, Response, content_types
from aws_lambda_powertools.event_handler.exceptions import ResponseSizeExceededError
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = ALBResolver(enable_response_size_validation=True)


@app.exception_handler(ResponseSizeExceededError)
def handle_large_response(error: ResponseSizeExceededError) -> Response:
    logger.error(
        "Response exceeds the ALB limit",
        actual_size=error.actual_size,
        max_size=error.max_size,
    )
    return Response(
        status_code=500,
        content_type=content_types.APPLICATION_JSON,
        body={"message": "Unable to return the response"},
    )


@app.get("/reports")
def get_report():
    return {"report": "Report contents"}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
