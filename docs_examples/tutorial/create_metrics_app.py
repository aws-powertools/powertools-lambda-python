import os

import boto3

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths

cold_start = True
metric_namespace = "MyApp"

logger = Logger(service="APP")
tracer = Tracer(service="APP")
metrics = boto3.client("cloudwatch")
app = APIGatewayRestResolver()


@tracer.capture_method
def add_greeting_metric(service: str = "APP"):
    function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME", "undefined")
    service_dimension = {"Name": "service", "Value": service}
    function_dimension = {"Name": "function_name", "Value": function_name}
    is_cold_start = True

    global cold_start
    if cold_start:
        cold_start = False
    else:
        is_cold_start = False

    return metrics.put_metric_data(
        MetricData=[
            {
                "MetricName": "SuccessfulGreetings",
                "Dimensions": [service_dimension],
                "Unit": "Count",
                "Value": 1,
            },
            {
                "MetricName": "ColdStart",
                "Dimensions": [service_dimension, function_dimension],
                "Unit": "Count",
                "Value": int(is_cold_start),
            },
        ],
        Namespace=metric_namespace,
    )


@app.get("/hello/<name>")
@tracer.capture_method
def hello_name(name):
    tracer.put_annotation(key="User", value=name)
    logger.info(f"Request from {name} received")
    add_greeting_metric()
    return {"message": f"hello {name}!"}


@app.get("/hello")
@tracer.capture_method
def hello():
    tracer.put_annotation(key="User", value="unknown")
    logger.info("Request from unknown received")
    add_greeting_metric()
    return {"message": "hello unknown!"}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
