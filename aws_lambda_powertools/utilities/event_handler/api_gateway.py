from enum import Enum
from typing import Any, Callable, Dict, List, Tuple, Union

from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext


class ProxyEventType(Enum):
    http_api_v1 = "APIGatewayProxyEvent"
    http_api_v2 = "APIGatewayProxyEventV2"
    alb_event = "ALBEvent"


class ApiGatewayResolver:
    def __init__(self, proxy_type: Enum = ProxyEventType.http_api_v1):
        self._proxy_type: Enum = proxy_type
        self._resolvers: List[Dict] = []

    def get(self, uri: str, include_event: bool = False, include_context: bool = False, **kwargs):
        return self.route("GET", uri, include_event, include_context, **kwargs)

    def post(self, uri: str, include_event: bool = False, include_context: bool = False, **kwargs):
        return self.route("POST", uri, include_event, include_context, **kwargs)

    def put(self, uri: str, include_event: bool = False, include_context: bool = False, **kwargs):
        return self.route("PUT", uri, include_event, include_context, **kwargs)

    def delete(self, uri: str, include_event: bool = False, include_context: bool = False, **kwargs):
        return self.route("DELETE", uri, include_event, include_context, **kwargs)

    def route(
        self,
        method: str,
        uri: str,
        include_event: bool = False,
        include_context: bool = False,
        **kwargs,
    ):
        def register_resolver(func: Callable[[Any, Any], Tuple[int, str, str]]):
            self._register(func, method.upper(), uri, include_event, include_context, kwargs)
            return func

        return register_resolver

    def resolve(self, event: Dict, context: LambdaContext) -> Dict:
        proxy_event: BaseProxyEvent = self._as_proxy_event(event)
        resolver: Callable[[Any], Tuple[int, str, str]]
        config: Dict
        resolver, config = self._find_resolver(proxy_event.http_method.upper(), proxy_event.path)
        kwargs = self._kwargs(proxy_event, context, config)
        result = resolver(**kwargs)
        return {"statusCode": result[0], "headers": {"Content-Type": result[1]}, "body": result[2]}

    def _register(
        self,
        func: Callable[[Any, Any], Tuple[int, str, str]],
        http_method: str,
        uri_starts_with: str,
        include_event: bool,
        include_context: bool,
        kwargs: Dict,
    ):
        kwargs["include_event"] = include_event
        kwargs["include_context"] = include_context
        self._resolvers.append(
            {
                "http_method": http_method,
                "uri_starts_with": uri_starts_with,
                "func": func,
                "config": kwargs,
            }
        )

    def _as_proxy_event(self, event: Dict) -> Union[ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2]:
        if self._proxy_type == ProxyEventType.http_api_v1:
            return APIGatewayProxyEvent(event)
        if self._proxy_type == ProxyEventType.http_api_v2:
            return APIGatewayProxyEventV2(event)
        return ALBEvent(event)

    def _find_resolver(self, http_method: str, path: str) -> Tuple[Callable, Dict]:
        for resolver in self._resolvers:
            expected_method = resolver["http_method"]
            if http_method != expected_method:
                continue
            path_starts_with = resolver["uri_starts_with"]
            if path.startswith(path_starts_with):
                return resolver["func"], resolver["config"]

        raise ValueError(f"No resolver found for '{http_method}.{path}'")

    @staticmethod
    def _kwargs(event: BaseProxyEvent, context: LambdaContext, config: Dict) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {}
        if config.get("include_event", False):
            kwargs["event"] = event
        if config.get("include_context", False):
            kwargs["context"] = context
        return kwargs

    def __call__(self, event, context) -> Any:
        return self.resolve(event, context)
