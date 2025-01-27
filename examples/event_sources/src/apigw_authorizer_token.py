from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerResponse,
    APIGatewayAuthorizerTokenEvent,
)


@event_source(data_class=APIGatewayAuthorizerTokenEvent)
def lambda_handler(event: APIGatewayAuthorizerTokenEvent, context):
    # Simple token check (replace with your actual token validation logic)
    is_valid_token = event.authorization_token == "allow"

    if not is_valid_token:
        return {"principalId": "", "policyDocument": {"Version": "2012-10-17", "Statement": []}}

    arn = event.parsed_arn

    policy = APIGatewayAuthorizerResponse(
        principal_id="user",
        context={"user": "example"},
        region=arn.region,
        aws_account_id=arn.aws_account_id,
        api_id=arn.api_id,
        stage=arn.stage,
    )

    policy.allow_all_routes()

    return policy.asdict()
