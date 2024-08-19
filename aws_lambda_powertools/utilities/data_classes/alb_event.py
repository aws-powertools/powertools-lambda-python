from __future__ import annotations

from typing import Any

from aws_lambda_powertools.shared.headers_serializer import (
    BaseHeadersSerializer,
    MultiValueHeadersSerializer,
    SingleValueHeadersSerializer,
)
from aws_lambda_powertools.utilities.data_classes.common import (
    BaseProxyEvent,
    CaseInsensitiveDict,
    DictWrapper,
)


class ALBEventRequestContext(DictWrapper):
    @property
    def elb_target_group_arn(self) -> str:
        """Target group arn for your Lambda function"""
        return self["requestContext"]["elb"]["targetGroupArn"]


class ALBEvent(BaseProxyEvent):
    """Application load balancer event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/services-alb.html
    - https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html
    """

    @property
    def request_context(self) -> ALBEventRequestContext:
        return ALBEventRequestContext(self._data)

    @property
    def multi_value_query_string_parameters(self) -> dict[str, list[str]]:
        return self.get("multiValueQueryStringParameters") or {}

    @property
    def resolved_query_string_parameters(self) -> dict[str, list[str]]:
        return self.multi_value_query_string_parameters or super().resolved_query_string_parameters

    @property
    def multi_value_headers(self) -> dict[str, list[str]]:
        return CaseInsensitiveDict(self.get("multiValueHeaders"))

    @property
    def resolved_headers_field(self) -> dict[str, Any]:
        return self.multi_value_headers or self.headers

    def header_serializer(self) -> BaseHeadersSerializer:
        # When using the ALB integration, the `multiValueHeaders` feature can be disabled (default) or enabled.
        # We can determine if the feature is enabled by looking if the event has a `multiValueHeaders` key.
        if self.multi_value_headers:
            return MultiValueHeadersSerializer()

        return SingleValueHeadersSerializer()
