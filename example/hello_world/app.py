import asyncio
import json

import aioboto3
import aiohttp
import requests

from aws_lambda_powertools import Logger, Metrics, Tracer, single_metric
from aws_lambda_powertools.logging.logger import set_package_logger
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.tracing import aiohttp_trace_config

set_package_logger()  # Enable package diagnostics (DEBUG log)

# tracer = Tracer() # patches all available modules
tracer = Tracer(patch_modules=("aioboto3", "boto3", "requests"))  # ~90-100ms faster in perf depending on set of libs
logger = Logger()
metrics = Metrics()

_cold_start = True

metrics.add_dimension(name="operation", value="example")  # added at cold start only


async def aioboto_task():
    async with aioboto3.client("sts") as sts:
        account = await sts.get_caller_identity()
        return account


async def aiohttp_task():
    # You have full access to all xray_recorder methods via `tracer.provider`
    # these include thread-safe methods, all context managers, x-ray configuration etc.
    # see https://github.com/aws/aws-xray-sdk-python/issues/164
    async with tracer.provider.in_subsegment_async("## aiohttp escape hatch"):
        async with aiohttp.ClientSession(trace_configs=[aiohttp_trace_config()]) as session:
            async with session.get("https://httpbin.org/json") as resp:
                resp = await resp.json()
                return resp


@tracer.capture_method
async def async_tasks():
    _, ret = await asyncio.gather(aioboto_task(), aiohttp_task(), return_exceptions=True)

    return {"task": "done", **ret}


@lambda_handler_decorator(trace_execution=True)
def my_middleware(handler, event, context, say_hello=False):
    if say_hello:
        print("========= HELLO PARAM DETECTED =========")
    print("========= Logging event before Handler is called =========")
    print(event)
    ret = handler(event, context)
    print("========= Logging response after Handler is called =========")
    print(ret)
    return ret


@tracer.capture_method
def func_1():
    return 1


@tracer.capture_method
def func_2():
    return 2


@tracer.capture_method
def sums_values():
    return func_1() + func_2()  # nested sync calls to reproduce issue #32


@metrics.log_metrics
@tracer.capture_lambda_handler
@my_middleware(say_hello=True)
@logger.inject_lambda_context
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
    sums_values()
    async_http_ret = asyncio.run(async_tasks())

    if "charge_id" in event:
        logger.structure_logs(append=True, payment_id="charge_id")

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
        logger.exception(e, exc_info=True)
        raise

    with single_metric(name="UniqueMetricDimension", unit="Seconds", value=1) as metric:
        metric.add_dimension(name="unique_dimension", value="for_unique_metric")

    resp = {"message": "hello world", "location": ip.text.replace("\n", ""), "async_http": async_http_ret}
    logger.info("Returning message to the caller")

    return {
        "statusCode": 200,
        "body": json.dumps(resp),
    }
