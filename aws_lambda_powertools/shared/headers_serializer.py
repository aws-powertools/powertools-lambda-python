import warnings
from collections import defaultdict
from typing import Any, Dict, List, Union

from aws_lambda_powertools.shared.cookies import Cookie


class BaseHeadersSerializer:
    """
    Helper class to correctly serialize headers and cookies for Amazon API Gateway,
    ALB and Lambda Function URL response payload.
    """

    def serialize(self, headers: Dict[str, Union[str, List[str]]], cookies: List[Cookie]) -> Dict[str, Any]:
        """
        Serializes headers and cookies according to the request type.
        Returns a dict that can be merged with the response payload.

        Parameters
        ----------
        headers: Dict[str, List[str]]
            A dictionary of headers to set in the response
        cookies: List[str]
            A list of cookies to set in the response
        """
        raise NotImplementedError()


class HttpApiHeadersSerializer(BaseHeadersSerializer):
    def serialize(self, headers: Dict[str, Union[str, List[str]]], cookies: List[Cookie]) -> Dict[str, Any]:
        """
        When using HTTP APIs or LambdaFunctionURLs, everything is taken care automatically for us.
        We can directly assign a list of cookies and a dict of headers to the response payload, and the
        runtime will automatically serialize them correctly on the output.

        https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html#http-api-develop-integrations-lambda.proxy-format
        https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html#http-api-develop-integrations-lambda.response
        """

        # Format 2.0 doesn't have multiValueHeaders or multiValueQueryStringParameters fields.
        # Duplicate headers are combined with commas and included in the headers field.
        combined_headers: Dict[str, str] = {}
        for key, values in headers.items():
            # omit headers with explicit null values
            if values is None:
                continue

            if isinstance(values, str):
                combined_headers[key] = values
            else:
                combined_headers[key] = ", ".join(values)

        return {"headers": combined_headers, "cookies": list(map(str, cookies))}


class MultiValueHeadersSerializer(BaseHeadersSerializer):
    def serialize(self, headers: Dict[str, Union[str, List[str]]], cookies: List[Cookie]) -> Dict[str, Any]:
        """
        When using REST APIs, headers can be encoded using the `multiValueHeaders` key on the response.
        This is also the case when using an ALB integration with the `multiValueHeaders` option enabled.
        The solution covers headers with just one key or multiple keys.

        https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-output-format
        https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html#multi-value-headers-response
        """
        payload: Dict[str, List[str]] = defaultdict(list)
        for key, values in headers.items():
            # omit headers with explicit null values
            if values is None:
                continue

            if isinstance(values, str):
                payload[key].append(values)
            else:
                payload[key].extend(values)

        if cookies:
            payload.setdefault("Set-Cookie", [])
            for cookie in cookies:
                payload["Set-Cookie"].append(str(cookie))

        return {"multiValueHeaders": payload}


class SingleValueHeadersSerializer(BaseHeadersSerializer):
    def serialize(self, headers: Dict[str, Union[str, List[str]]], cookies: List[Cookie]) -> Dict[str, Any]:
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
                    "Can't encode more than one cookie in the response. Sending the last cookie only. "
                    "Did you enable multiValueHeaders on the ALB Target Group?",
                    stacklevel=2,
                )

            # We can only send one cookie, send the last one
            payload["headers"]["Set-Cookie"] = str(cookies[-1])

        for key, values in headers.items():
            # omit headers with explicit null values
            if values is None:
                continue

            if isinstance(values, str):
                payload["headers"][key] = values
            else:
                if len(values) > 1:
                    warnings.warn(
                        f"Can't encode more than one header value for the same key ('{key}') in the response. "
                        "Did you enable multiValueHeaders on the ALB Target Group?",
                        stacklevel=2,
                    )

                # We can only set one header per key, send the last one
                payload["headers"][key] = values[-1]

        return payload
