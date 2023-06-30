import boto3
import unwrapping_popular_event_source_schema as schemas
from botocore.exceptions import ClientError

from aws_lambda_powertools.utilities.data_classes.event_bridge_event import (
    EventBridgeEvent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import envelopes, validator


# extracting detail from EventBridge custom event
# see: https://docs.powertools.aws.dev/lambda/python/latest/utilities/jmespath_functions/#built-in-envelopes
@validator(inbound_schema=schemas.INPUT, envelope=envelopes.EVENTBRIDGE)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    my_event = EventBridgeEvent(event)
    ec2_client = boto3.resource("ec2", region_name=my_event.region)

    try:
        instance_id = my_event.detail.get("instance_id")
        instance = ec2_client.Instance(instance_id)
        instance.stop()

        return {"message": f"Successfully stopped {instance_id}", "success": True}
    except ClientError as exception:
        return {"message": str(exception), "success": False}
