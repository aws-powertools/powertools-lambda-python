from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(strip_prefixes=["/payment"])


@app.get("/subscriptions/<subscription>")
@tracer.capture_method
def get_subscription(subscription):
    return {"subscription_id": subscription}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    return app.resolve(event, context)
