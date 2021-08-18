from typing import Any, Dict, List, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class RequestContextV2(DictWrapper):
    ...


class ApiGatewayAuthorizerV2Event(DictWrapper):
    """API Gateway Authorizer Format 2.0

    Documentation:
    -------------
    - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html
    """

    @property
    def version(self) -> str:
        return self["version"]

    @property
    def get_type(self) -> str:
        return self["type"]

    @property
    def route_arn(self) -> str:
        return self["routeArn"]

    @property
    def identity_source(self) -> List[str]:
        return self["identitySource"]

    @property
    def route_key(self) -> str:
        return self["routeKey"]

    @property
    def raw_path(self) -> str:
        return self["rawPath"]

    @property
    def raw_query_string(self) -> str:
        return self["rawQueryString"]

    @property
    def cookies(self) -> List[str]:
        return self["cookies"]

    @property
    def headers(self) -> Dict[str, str]:
        return self["headers"]

    @property
    def query_string_parameters(self) -> Dict[str, str]:
        return self["queryStringParameters"]

    @property
    def request_pontext(self) -> RequestContextV2:
        return RequestContextV2(self._data)

    @property
    def path_parameters(self) -> Dict[str, str]:
        return self["pathParameters"]

    @property
    def stage_variables(self) -> Dict[str, str]:
        return self["stageVariables"]


class ApiGatewayAuthorizerSimpleResponse:
    """Api Gateway HTTP API V2 payload authorizer simple response helper

    Parameters
    ----------
    authorize: bool
        authorize is a boolean value indicating if the value in authorizationToken
        is authorized to make calls to the GraphQL API. If this value is
        true, execution of the GraphQL API continues. If this value is false,
        an UnauthorizedException is raised
    context: Dict[str, Any], optional
        A JSON object visible as `event.requestContext.authorizer` lambda event

        The context object only supports key-value pairs. Nested keys are not supported.

        Warning: The total size of this JSON object must not exceed 5MB.

    """

    def __init__(
        self,
        authorize: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.authorize = authorize
        self.context = context

    def asdict(self) -> dict:
        """Return the response as a dict"""
        response: Dict = {"isAuthorized": self.authorize}

        if self.context:
            response["context"] = self.context

        return response
