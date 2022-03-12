from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths

logger = Logger()
app = APIGatewayRestResolver()  # API Gateway REST API (v1)


@app.get("/hello")
def get_hello_universe():
    return {"message": "hello universe"}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def lambda_handler(event, context):
    return app.resolve(event, context)
