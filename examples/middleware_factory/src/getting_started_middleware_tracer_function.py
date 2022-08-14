import time
from typing import Callable

import requests
from requests import Response

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver()


@lambda_handler_decorator(trace_execution=True)
def middleware_with_tracing(handler, event, context) -> Callable:

    start_time = time.time()
    response = handler(event, context)
    execution_time = time.time() - start_time

    # adding custom headers in response object after lambda executing
    response["headers"]["execution_time"] = execution_time
    response["headers"]["aws_request_id"] = context.aws_request_id

    return response


@app.get("/products")
def create_product() -> dict:
    product: Response = requests.get("https://dummyjson.com/products/1")
    product.raise_for_status()

    return {"product": product.json()}


@middleware_with_tracing
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
