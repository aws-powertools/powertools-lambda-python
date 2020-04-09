import json

from aws_lambda_powertools.logging import logger_inject_lambda_context, logger_setup
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.metrics import Metrics, MetricUnit, single_metric
import requests

tracer = Tracer()
logger = logger_setup()
metrics = Metrics()

_cold_start = True

metrics.add_dimension(name="operation", value="example")

@metrics.log_metrics
@tracer.capture_lambda_handler
@logger_inject_lambda_context
def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    global _cold_start
    if _cold_start:
        logger.debug("Recording cold start metric")
        metrics.add_metric(name="ColdStart", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="function_name", value=context.function_name)            
        _cold_start = False

    try:
        ip = requests.get("http://checkip.amazonaws.com/")
        metrics.add_metric(name="SuccessfulLocations", unit="Count", value=1)
    except requests.RequestException as e:
        # Send some context about this error to Lambda Logs
        logger.error(e)
        raise e
    
    logger.info("Returning message to the caller")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            "location": ip.text.replace("\n", "")
        }),
    }
