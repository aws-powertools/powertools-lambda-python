import warnings
from abc import ABC
from typing import Any, Dict, List


class BaseHeadersSerializer(ABC):
    """
    Helper class to correctly serialize headers and cookies on the response payload.
    """

    def serialize(self, headers: Dict[str, str], cookies: List[str]) -> Dict[str, Any]:
        """
        Serializes headers and cookies according to the request type.
        Returns a dict that can be merged with the response payload.

        Parameters
        ----------
        headers: Dict[str, str]
            A dictionary of headers to set in the response
        cookies: List[str]
            A list of cookies to set in the response
        """
        raise NotImplementedError()


class HttpApiSerializer(BaseHeadersSerializer):
    def serialize(self, headers: Dict[str, str], cookies: List[str]) -> Dict[str, Any]:
        """
        When using HTTP APIs or LambdaFunctionURLs, everything is taken care automatically for us.
        We can directly assign a list of cookies and a dict of headers to the response payload, and the
        runtime will automatically serialize them correctly on the output.

        https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html#http-api-develop-integrations-lambda.proxy-format
        https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html#http-api-develop-integrations-lambda.response
        """
        return {"headers": headers, "cookies": cookies}


class MultiValueHeadersSerializer(BaseHeadersSerializer):
    def serialize(self, headers: Dict[str, str], cookies: List[str]) -> Dict[str, Any]:
        """
        When using REST APIs, headers can be encoded using the `multiValueHeaders` key on the response.
        This is also the case when using an ALB integration with the `multiValueHeaders` option enabled.
        The solution covers headers with just one key or multiple keys.

        https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-output-format
        https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html#multi-value-headers-response
        """
        payload: Dict[str, List[str]] = {}

        for key, value in headers.items():
            values = value.split(",")
            payload[key] = [value.strip() for value in values]

        if cookies:
            payload.setdefault("Set-Cookie", [])
            for cookie in cookies:
                payload["Set-Cookie"].append(cookie)

        return {"multiValueHeaders": payload}


class SingleValueHeadersSerializer(BaseHeadersSerializer):
    def serialize(self, headers: Dict[str, str], cookies: List[str]) -> Dict[str, Any]:
        """
        The ALB integration has `multiValueHeaders` disabled by default.
        If we try to set multiple headers with the same key, or more than one cookie, print a warning.

        https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html#respond-to-load-balancer
        """
        payload: Dict[str, Dict[str, str]] = {}
        payload.setdefault("headers", {})

        if cookies:
            if len(cookies) > 1:
                warnings.warn(
                    "Can't encode more than one cookie in the response. "
                    "Did you enable multiValueHeaders on the ALB Target Group?"
                )

            # We can only send one cookie, send the last one
            payload["headers"]["Set-Cookie"] = cookies[-1]

        for key, value in headers.items():
            values = value.split(",")
            if len(values) > 1:
                warnings.warn(
                    "Can't encode more than on header with the same key in the response. "
                    "Did you enable multiValueHeaders on the ALB Target Group?"
                )

            # We can only send on header for this key, send the last value
            payload["headers"][key] = values[-1].strip()

        return payload
