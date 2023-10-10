import os
from pathlib import Path

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.api_gateway import (
    APIGatewayRestResolver,
    Response,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()


app = APIGatewayRestResolver()
logo_file: bytes = Path(f"{os.getenv('LAMBDA_TASK_ROOT')}/logo.svg").read_bytes()


@app.get("/logo")
@tracer.capture_method
def get_logo():
    return Response(status_code=200, content_type="image/svg+xml", body=logo_file)


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
