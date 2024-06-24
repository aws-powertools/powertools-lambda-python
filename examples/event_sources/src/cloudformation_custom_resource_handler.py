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
        return on_create(event)
    if request_type == "Update":
        return on_update(event)
    if request_type == "Delete":
        return on_delete(event)


def on_create(event: CloudFormationCustomResourceEvent):
    props = event.resource_properties
    logger.info(f"Create new resource with props {props}.")

    # Add your create code here ...
    physical_id = ...

    return {"PhysicalResourceId": physical_id}


def on_update(event: CloudFormationCustomResourceEvent):
    physical_id = event.physical_resource_id
    props = event.resource_properties
    logger.info(f"Update resource {physical_id} with props {props}.")
    # ...


def on_delete(event: CloudFormationCustomResourceEvent):
    physical_id = event.physical_resource_id
    logger.info(f"Delete resource {physical_id}.")
    # ...
