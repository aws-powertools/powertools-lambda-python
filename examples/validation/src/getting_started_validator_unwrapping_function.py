import boto3
import getting_started_validator_unwrapping_schema as schemas

from aws_lambda_powertools.utilities.data_classes.event_bridge_event import (
    EventBridgeEvent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import validator

s3_client = boto3.resource("s3")


# we use the 'envelope' parameter to extract the payload inside the 'detail' key before validating
@validator(inbound_schema=schemas.INPUT, envelope="detail")
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    my_event = EventBridgeEvent(event)
    data = my_event.detail.get("data", {})
    s3_bucket, s3_key = data.get("s3_bucket"), data.get("s3_key")

    try:
        s3_object = s3_client.Object(bucket_name=s3_bucket, key=s3_key)
        payload = s3_object.get()["Body"]
        content = payload.read().decode("utf-8")

        return {"message": process_data_object(content), "success": True}
    except s3_client.meta.client.exceptions.NoSuchBucket as exception:
        return return_error_message(str(exception))
    except s3_client.meta.client.exceptions.NoSuchKey as exception:
        return return_error_message(str(exception))


def return_error_message(message: str) -> dict:
    return {"message": message, "success": False}


def process_data_object(content: str) -> str:
    # insert logic here
    return "Data OK"
