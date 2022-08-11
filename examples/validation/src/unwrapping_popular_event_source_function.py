import boto3
import unwrapping_popular_event_source_schema as schemas
from botocore.exceptions import ClientError

from aws_lambda_powertools.utilities.validation import envelopes, validator


# extracting detail from eventbridge custom event
@validator(inbound_schema=schemas.INPUT, envelope=envelopes.EVENTBRIDGE)
def lambda_handler(event, context):
    try:
        ec2_client = boto3.resource("ec2", region_name=event.get("region"))
        instance_id = event.get("instance_id")
        instance = ec2_client.Instance(instance_id)
        instance.stop()

        return {"message": f"Successfully stopped {instance_id}", "success": True}

    except ClientError as exception:
        return {"message": str(exception), "success": False}
