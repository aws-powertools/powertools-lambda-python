from aws_xray_sdk.core import patch_all, xray_recorder

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths

logger = Logger(service="APP")

app = APIGatewayRestResolver()
cold_start = True
patch_all()


@app.get("/hello/<name>")
@xray_recorder.capture("hello_name")
def hello_name(name):
    subsegment = xray_recorder.current_subsegment()
    subsegment.put_annotation(key="User", value=name)
    logger.info(f"Request from {name} received")
    return {"message": f"hello {name}!"}


@app.get("/hello")
@xray_recorder.capture("hello")
def hello():
    subsegment = xray_recorder.current_subsegment()
    subsegment.put_annotation(key="User", value="unknown")
    logger.info("Request from unknown received")
    return {"message": "hello unknown!"}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST, log_event=True)
@xray_recorder.capture("handler")
def lambda_handler(event, context):
    global cold_start

    subsegment = xray_recorder.current_subsegment()
    if cold_start:
        subsegment.put_annotation(key="ColdStart", value=cold_start)
        cold_start = False
    else:
        subsegment.put_annotation(key="ColdStart", value=cold_start)

    result = app.resolve(event, context)
    subsegment.put_metadata("response", result)

    return result
