from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import (
    CloudFormationCustomResourceEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@event_source(data_class=CloudFormationCustomResourceEvent)
def lambda_handler(event: CloudFormationCustomResourceEvent, context: LambdaContext):
    request_type = event.request_type

    if request_type == "Create":
        return on_create(event, context)
    else:
        raise ValueError(f"Invalid request type: {request_type}")


def on_create(event: CloudFormationCustomResourceEvent, context: LambdaContext):
    props = event.resource_properties
    logger.info(f"Create new resource with props {props}.")

    physical_id = f"MyResource-{context.aws_request_id}"

    return {"PhysicalResourceId": physical_id, "Data": {"Message": "Resource created successfully"}}
