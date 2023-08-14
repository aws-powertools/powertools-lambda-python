import re

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

# This will support:
# /v1/dev/subscriptions/<subscription>
# /v1/stg/subscriptions/<subscription>
# /v1/qa/subscriptions/<subscription>
# /v2/dev/subscriptions/<subscription>
# ...
app = APIGatewayRestResolver(strip_prefixes=[re.compile(r"/v[1-3]+/(dev|stg|qa)")])


@app.get("/subscriptions/<subscription>")
def get_subscription(subscription):
    return {"subscription_id": subscription}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
