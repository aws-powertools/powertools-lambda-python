import warnings
from typing import Any, Dict, List

from aws_lambda_powertools.utilities.data_classes import (
    ALBEvent,
    APIGatewayProxyEvent,
    APIGatewayProxyEventV2,
    LambdaFunctionUrlEvent,
)
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent


class HeadersSerializer:
    """
    Helper class to correctly serialize headers and cookies on the response payload.
    """

    def __init__(self, event: BaseProxyEvent, cookies: List[str], headers: Dict[str, str]):
        """

        Parameters
        ----------
        event: BaseProxyEvent
            The request event, used to derive the response format
        cookies: List[str]
            A list of cookies to set in the response
        headers: Dict[str, str]
            A dictionary of headers to set in the response
        """
        self.event = event
        self.cookies = cookies
        self.headers = headers

    def serialize(self) -> Dict[str, Any]:
        """
        Serializes headers and cookies according to the request type.
        Returns a dict that can be merged with the response payload.
        """
        payload: Dict[str, Any] = {}

        if isinstance(self.event, APIGatewayProxyEventV2) or isinstance(self.event, LambdaFunctionUrlEvent):
            """
            When using HTTP APIs or LambdaFunctionURLs, everything is taken care automatically.
            One can directly assign a list of cookies and a dict of headers to the response payload, and the
            runtime will automatically serialize them correctly on the output.

            https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html#http-api-develop-integrations-lambda.proxy-format
            https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html#http-api-develop-integrations-lambda.response
            """
            payload["cookies"] = self.cookies
            payload["headers"] = self.headers

        if isinstance(self.event, APIGatewayProxyEvent):
            """
            When using REST APIs, headers can be encoded using the "multiValueHeaders" key on the response.
            This will cover both single and multi-value headers.

            https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-output-format
            """

            payload["multiValueHeaders"] = self._build_multivalue_headers()

        if isinstance(self.event, ALBEvent):
            """
            The ALB integration can work with multiValueHeaders disabled (default) or enabled.
            We can detect if the feature is enabled by looking for the presence of `multiValueHeaders` in the request.
            If the feature is disabled, and we try to set multiple headers with the same key, or more than one cookie,
            print a warning.


            https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html#respond-to-load-balancer
            https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html#multi-value-headers-response
            """
            if self.event.multi_value_headers is not None:
                payload["multiValueHeaders"] = self._build_multivalue_headers()
            else:
                payload.setdefault("headers", {})

                if self.cookies:
                    if len(self.cookies) > 1:
                        warnings.warn(
                            "Can't encode more than one cookie in the response. "
                            "Did you enable multiValueHeaders on the ALB Target Group?"
                        )

                    # We can only send one cookie, send the last one
                    payload["headers"]["Set-Cookie"] = self.cookies[-1]

                for key, value in self.headers.items():
                    values = value.split(",")
                    if len(values) > 1:
                        warnings.warn(
                            "Can't encode more than on header with the same key in the response. "
                            "Did you enable multiValueHeaders on the ALB Target Group?"
                        )

                    # We can only send on header for this key, send the last value
                    payload["headers"][key] = values[-1].strip()

        return payload

    def _build_multivalue_headers(self) -> Dict[str, List[str]]:
        """Formats headers and cookies according to the `multiValueHeader` format"""
        multi_value_headers: Dict[str, List[str]] = {}

        for key, value in self.headers.items():
            values = value.split(",")
            multi_value_headers[key] = [value.strip() for value in values]

        if self.cookies:
            multi_value_headers.setdefault("Set-Cookie", [])
            for cookie in self.cookies:
                multi_value_headers["Set-Cookie"].append(cookie)

        return multi_value_headers
