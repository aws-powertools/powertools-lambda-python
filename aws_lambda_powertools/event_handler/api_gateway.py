import re
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext


class ProxyEventType(Enum):
    http_api_v1 = "APIGatewayProxyEvent"
    http_api_v2 = "APIGatewayProxyEventV2"
    alb_event = "ALBEvent"
    api_gateway = http_api_v1


class RouteEntry:
    def __init__(self, method: str, rule: Any, func: Callable, cors: bool):
        self.method = method.upper()
        self.rule = rule
        self.func = func
        self.cors = cors


class ApiGatewayResolver:
    current_event: BaseProxyEvent
    lambda_context: LambdaContext

    def __init__(self, proxy_type: Enum = ProxyEventType.http_api_v1):
        self._proxy_type = proxy_type
        self._routes: List[RouteEntry] = []

    def get(self, rule: str, cors: bool = False):
        return self.route(rule, "GET", cors)

    def post(self, rule: str, cors: bool = False):
        return self.route(rule, "POST", cors)

    def put(self, rule: str, cors: bool = False):
        return self.route(rule, "PUT", cors)

    def delete(self, rule: str, cors: bool = False):
        return self.route(rule, "DELETE", cors)

    def route(self, rule: str, method: str, cors: bool = False):
        def register_resolver(func: Callable):
            self._register(func, rule, method, cors)
            return func

        return register_resolver

    def resolve(self, event: Dict, context: LambdaContext) -> Dict:
        self.current_event = self._as_data_class(event)
        self.lambda_context = context

        route, args = self._find_route(self.current_event.http_method, self.current_event.path)

        result = route.func(**args)

        headers = {"Content-Type": result[1]}
        if route.cors:
            headers["Access-Control-Allow-Origin"] = "*"
            headers["Access-Control-Allow-Methods"] = route.method
            headers["Access-Control-Allow-Credentials"] = "true"

        return {"statusCode": result[0], "headers": headers, "body": result[2]}

    def _register(self, func: Callable, rule: str, method: str, cors: bool):
        self._routes.append(RouteEntry(method, self._build_rule_pattern(rule), func, cors))

    @staticmethod
    def _build_rule_pattern(rule: str):
        rule_regex: str = re.sub(r"(<\w+>)", r"(?P\1.+)", rule)
        return re.compile("^{}$".format(rule_regex))

    def _as_data_class(self, event: Dict) -> BaseProxyEvent:
        if self._proxy_type == ProxyEventType.http_api_v1:
            return APIGatewayProxyEvent(event)
        if self._proxy_type == ProxyEventType.http_api_v2:
            return APIGatewayProxyEventV2(event)
        return ALBEvent(event)

    def _find_route(self, method: str, path: str) -> Tuple[RouteEntry, Dict]:
        method = method.upper()
        for resolver in self._routes:
            if method != resolver.method:
                continue
            match: Optional[re.Match] = resolver.rule.match(path)
            if match:
                return resolver, match.groupdict()

        raise ValueError(f"No route found for '{method}.{path}'")

    def __call__(self, event, context) -> Any:
        return self.resolve(event, context)
