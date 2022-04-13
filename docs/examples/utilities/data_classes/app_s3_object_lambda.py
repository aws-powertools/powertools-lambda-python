import boto3
import requests

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.correlation_paths import S3_OBJECT_LAMBDA
from aws_lambda_powertools.utilities.data_classes.s3_object_event import S3ObjectLambdaEvent

logger = Logger()
session = boto3.Session()
s3 = session.client("s3")


@logger.inject_lambda_context(correlation_id_path=S3_OBJECT_LAMBDA, log_event=True)
def lambda_handler(event, context):
    event = S3ObjectLambdaEvent(event)

    # Get object from S3
    response = requests.get(event.input_s3_url)
    original_object = response.content.decode("utf-8")

    # Make changes to the object about to be returned
    transformed_object = original_object.upper()

    # Write object back to S3 Object Lambda
    s3.write_get_object_response(
        Body=transformed_object,
        RequestRoute=event.request_route,
        RequestToken=event.request_token,
    )

    return {"status_code": 200}
