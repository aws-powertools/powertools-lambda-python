import json
from typing import Callable

import boto3
import combining_powertools_utilities_schema as schemas
import requests

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.exceptions import InternalServerError
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.shared.types import JSONType
from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.jmespath_utils import extract_data_from_envelope
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import SchemaValidationError, validate

app = APIGatewayRestResolver()
tracer = Tracer()
logger = Logger()

table_historic = boto3.resource("dynamodb").Table("HistoricTable")

app_config = AppConfigStore(environment="dev", application="comments", name="features")
feature_flags = FeatureFlags(store=app_config)


@lambda_handler_decorator(trace_execution=True)
def middleware_custom(handler: Callable, event: dict, context: LambdaContext):

    # validating the INPUT with the given schema
    # X-Customer-Id header must be informed in all requests
    try:
        validate(event=event, schema=schemas.INPUT)
    except SchemaValidationError as e:
        return {
            "statusCode": 400,
            "body": json.dumps(str(e)),
        }

    # extracting headers and requestContext from event
    headers = extract_data_from_envelope(data=event, envelope="headers")
    request_context = extract_data_from_envelope(data=event, envelope="requestContext")

    logger.debug(f"X-Customer-Id => {headers.get('X-Customer-Id')}")
    tracer.put_annotation(key="CustomerId", value=headers.get("X-Customer-Id"))

    response = handler(event, context)

    # automatically adding security headers to all responses
    # see: https://securityheaders.com/
    logger.info("Injecting security headers")
    response["headers"]["Referrer-Policy"] = "no-referrer"
    response["headers"]["Strict-Transport-Security"] = "max-age=15552000; includeSubDomains; preload"
    response["headers"]["X-DNS-Prefetch-Control"] = "off"
    response["headers"]["X-Content-Type-Options"] = "nosniff"
    response["headers"]["X-Permitted-Cross-Domain-Policies"] = "none"
    response["headers"]["X-Download-Options"] = "noopen"

    logger.info("Saving api call in history table")
    save_api_execution_history(str(event.get("path")), headers, request_context)

    # return lambda execution
    return response


@tracer.capture_method
def save_api_execution_history(path: str, headers: dict, request_context: dict) -> None:

    try:
        # using the feature flags utility to check if the new feature "save api call to history" is enabled by default
        # see: https://awslabs.github.io/aws-lambda-powertools-python/latest/utilities/feature_flags/#static-flags
        save_history: JSONType = feature_flags.evaluate(name="save_history", default=False)
        if save_history:
            # saving history in dynamodb table
            tracer.put_metadata(key="execution detail", value=request_context)
            table_historic.put_item(
                Item={
                    "customer_id": headers.get("X-Customer-Id"),
                    "request_id": request_context.get("requestId"),
                    "path": path,
                    "request_time": request_context.get("requestTime"),
                    "source_ip": request_context.get("identity", {}).get("sourceIp"),
                    "http_method": request_context.get("httpMethod"),
                }
            )

        return None
    except Exception:
        # you can add more logic here to handle exceptions or even save this to a DLQ
        # but not to make this example too long, we just return None since the Lambda has been successfully executed
        return None


@app.get("/comments")
@tracer.capture_method
def get_comments():
    try:
        comments: requests.Response = requests.get("https://jsonplaceholder.typicode.com/comments")
        comments.raise_for_status()

        return {"comments": comments.json()[:10]}
    except Exception as exc:
        raise InternalServerError(str(exc))


@app.get("/comments/<comment_id>")
@tracer.capture_method
def get_comments_by_id(comment_id: str):
    try:
        comments: requests.Response = requests.get(f"https://jsonplaceholder.typicode.com/comments/{comment_id}")
        comments.raise_for_status()

        return {"comments": comments.json()}
    except Exception as exc:
        raise InternalServerError(str(exc))


@middleware_custom
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
