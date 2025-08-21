from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.get("/users/<user_id>")
@tracer.capture_method
def get_user(user_id: str):
    # user_id value comes as a string with special chars support
    return {"user_id": user_id}


@app.get("/orders/<order_id>/items/<item_id>")
@tracer.capture_method
def get_order_item(order_id: str, item_id: str):
    # multiple dynamic parameters are supported
    return {"order_id": order_id, "item_id": item_id}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
