from secrets import compare_digest

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    DENY_ALL_RESPONSE,
    APIGatewayAuthorizerRequestEvent,
    APIGatewayAuthorizerResponse,
    HttpVerb,
)


def get_user_by_token(token):
    if compare_digest(token, "admin-foo"):
        return {"id": 0, "name": "Admin", "isAdmin": True}
    elif compare_digest(token, "regular-foo"):
        return {"id": 1, "name": "Joe"}
    else:
        return None


@event_source(data_class=APIGatewayAuthorizerRequestEvent)
def handler(event: APIGatewayAuthorizerRequestEvent, context):
    user = get_user_by_token(event.get_header_value("Authorization"))

    if user is None:
        # No user was found
        # to return 401 - `{"message":"Unauthorized"}`, but pollutes lambda error count metrics
        # raise Exception("Unauthorized")
        # to return 403 - `{"message":"Forbidden"}`
        return DENY_ALL_RESPONSE

    # parse the `methodArn` as an `APIGatewayRouteArn`
    arn = event.parsed_arn

    # Create the response builder from parts of the `methodArn`
    # and set the logged in user id and context
    policy = APIGatewayAuthorizerResponse(
        principal_id=user["id"],
        context=user,
        region=arn.region,
        aws_account_id=arn.aws_account_id,
        api_id=arn.api_id,
        stage=arn.stage,
    )

    # Conditional IAM Policy
    if user.get("isAdmin", False):
        policy.allow_all_routes()
    else:
        policy.allow_route(HttpVerb.GET, "/user-profile")

    return policy.asdict()
