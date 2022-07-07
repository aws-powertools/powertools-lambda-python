import datetime
import json
import os
from importlib.metadata import version

import boto3

from aws_lambda_powertools import Logger, Metrics, Tracer

logger = Logger(service="version-track")
tracer = Tracer()
metrics = Metrics(namespace="powertools-layer-canary", service="PowertoolsLayerCanary")

layer_arn = os.getenv("POWERTOOLS_LAYER_ARN")
powertools_version = os.getenv("POWERTOOLS_VERSION")
stage = os.getenv("LAYER_PIPELINE_STAGE")
event_bus_arn = os.getenv("VERSION_TRACKING_EVENT_BUS_ARN")


def handler(event):
    logger.info("Running checks")
    check_envs()
    verify_powertools_version()
    send_notification()
    return True


@logger.inject_lambda_context(log_event=True)
def on_event(event, context):
    request_type = event["RequestType"]
    # we handle only create events, because we recreate the canary on each run
    if request_type == "Create":
        return on_create(event)

    return "Nothing to be processed"


def on_create(event):
    props = event["ResourceProperties"]
    logger.info("create new resource with properties %s" % props)
    handler(event)


def check_envs():
    logger.info('Checking required envs ["POWERTOOLS_LAYER_ARN", "AWS_REGION", "STAGE"]')
    if not layer_arn:
        raise ValueError("POWERTOOLS_LAYER_ARN is not set. Aborting...")
    if not powertools_version:
        raise ValueError("POWERTOOLS_VERSION is not set. Aborting...")
    if not stage:
        raise ValueError("LAYER_PIPELINE_STAGE is not set. Aborting...")
    if not event_bus_arn:
        raise ValueError("VERSION_TRACKING_EVENT_BUS_ARN is not set. Aborting...")
    logger.info("All envs configured, continue...")


def verify_powertools_version() -> None:
    """
    fetches the version that we import from the powertools layer and compares
    it with expected version set in environment variable, which we pass during deployment.
    :raise ValueError if the expected version is not the same as the version we get from the layer
    """
    logger.info("Checking Powertools version in library...")
    current_version = version("aws_lambda_powertools")
    if powertools_version != current_version:
        raise ValueError(
            f'Expected powertoosl version is "{powertools_version}", but layer contains version "{current_version}"'
        )
    logger.info(f"Current Powertools version is: {current_version}")


def send_notification():
    """
    sends an event to version tracking event bridge
    """
    event = {
        "Time": datetime.datetime.now(),
        "Source": "powertools.layer.canary",
        "EventBusName": event_bus_arn,
        "DetailType": "deployment",
        "Detail": json.dumps(
            {
                "id": "powertools-python",
                "stage": stage,
                "region": os.environ["AWS_REGION"],
                "version": powertools_version,
                "layerArn": layer_arn,
            }
        ),
    }

    logger.info(f"sending notification event: {event}")

    client = boto3.client("events", region_name="eu-central-1")
    resp = client.put_events(Entries=[event])
    logger.info(resp)
    if resp["FailedEntryCount"] != 0:
        logger.error(resp)
        raise ValueError("Failed to send deployment notification to version tracking")
