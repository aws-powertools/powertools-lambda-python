from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerRequestEvent,
    APIGatewayAuthorizerResponseWebSocket,
)


@event_source(data_class=APIGatewayAuthorizerRequestEvent)
def lambda_handler(event: APIGatewayAuthorizerRequestEvent, context):
    # Simple auth check (replace with your actual auth logic)
    is_authorized = event.headers.get("HeaderAuth1") == "headerValue1"

    if not is_authorized:
        return {"principalId": "", "policyDocument": {"Version": "2012-10-17", "Statement": []}}

    arn = event.parsed_arn

    policy = APIGatewayAuthorizerResponseWebSocket(
        principal_id="user",
        context={"user": "example"},
        region=arn.region,
        aws_account_id=arn.aws_account_id,
        api_id=arn.api_id,
        stage=arn.stage,
    )

    policy.allow_all_routes()

    return policy.asdict()
