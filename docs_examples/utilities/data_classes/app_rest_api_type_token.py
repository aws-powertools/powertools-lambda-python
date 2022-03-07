from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerResponse,
    APIGatewayAuthorizerTokenEvent,
)


@event_source(data_class=APIGatewayAuthorizerTokenEvent)
def handler(event: APIGatewayAuthorizerTokenEvent, context):
    arn = event.parsed_arn

    policy = APIGatewayAuthorizerResponse(
        principal_id="user",
        region=arn.region,
        aws_account_id=arn.aws_account_id,
        api_id=arn.api_id,
        stage=arn.stage,
    )

    if event.authorization_token == "42":
        policy.allow_all_routes()
    else:
        policy.deny_all_routes()
    return policy.asdict()
