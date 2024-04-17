from typing import Any, Dict, List, Optional

from aws_lambda_powertools.shared.headers_serializer import (
    BaseHeadersSerializer,
    MultiValueHeadersSerializer,
    SingleValueHeadersSerializer,
)
from aws_lambda_powertools.utilities.data_classes.common import (
    BaseProxyEvent,
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
    def multi_value_query_string_parameters(self) -> Dict[str, List[str]]:
        return self.get("multiValueQueryStringParameters") or {}

    @property
    def resolved_query_string_parameters(self) -> Dict[str, List[str]]:
        if self.multi_value_query_string_parameters:
            return self.multi_value_query_string_parameters

        return super().resolved_query_string_parameters

    @property
    def resolved_headers_field(self) -> Dict[str, Any]:
        headers: Dict[str, Any] = {}

        if self.multi_value_headers:
            headers = self.multi_value_headers
        else:
            headers = self.headers

        return {key.lower(): value for key, value in headers.items()}

    @property
    def multi_value_headers(self) -> Optional[Dict[str, List[str]]]:
        return self.get("multiValueHeaders")

    def header_serializer(self) -> BaseHeadersSerializer:
        # When using the ALB integration, the `multiValueHeaders` feature can be disabled (default) or enabled.
        # We can determine if the feature is enabled by looking if the event has a `multiValueHeaders` key.
        if self.multi_value_headers:
            return MultiValueHeadersSerializer()

        return SingleValueHeadersSerializer()
