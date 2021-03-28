import re
from enum import Enum
from typing import Any, Callable, Dict, List, Tuple

from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext


class ProxyEventType(Enum):
    http_api_v1 = "APIGatewayProxyEvent"
    http_api_v2 = "APIGatewayProxyEventV2"
    alb_event = "ALBEvent"


class ApiGatewayResolver:
    current_request: BaseProxyEvent
    lambda_context: LambdaContext

    def __init__(self, proxy_type: Enum = ProxyEventType.http_api_v1):
        self._proxy_type = proxy_type
        self._resolvers: List[Dict] = []

    def get(self, rule: str):
        return self.route("GET", rule)

    def post(self, rule: str):
        return self.route("POST", rule)

    def put(self, rule: str):
        return self.route("PUT", rule)

    def delete(self, rule: str):
        return self.route("DELETE", rule)

    def route(self, method: str, rule: str):
        def register_resolver(func: Callable[[Any, Any], Tuple[int, str, str]]):
            self._register(func, method.upper(), rule)
            return func

        return register_resolver

    def resolve(self, event: Dict, context: LambdaContext) -> Dict:
        self.current_request = self._as_proxy_event(event)
        self.lambda_context = context
        resolver: Callable[[Any], Tuple[int, str, str]]
        resolver, args = self._find_resolver(self.current_request.http_method.upper(), self.current_request.path)
        result = resolver(**args)
        return {"statusCode": result[0], "headers": {"Content-Type": result[1]}, "body": result[2]}

    def _register(self, func: Callable[[Any, Any], Tuple[int, str, str]], http_method: str, rule: str):
        self._resolvers.append(
            {"http_method": http_method, "rule_pattern": self._build_rule_pattern(rule), "func": func}
        )

    @staticmethod
    def _build_rule_pattern(rule: str):
        rule_regex: str = re.sub(r"(<\w+>)", r"(?P\1.+)", rule)
        return re.compile("^{}$".format(rule_regex))

    def _as_proxy_event(self, event: Dict) -> BaseProxyEvent:
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
            match = resolver["rule_pattern"].match(path)
            if match:
                return resolver["func"], match.groupdict()

        raise ValueError(f"No resolver found for '{http_method}.{path}'")

    def __call__(self, event, context) -> Any:
        return self.resolve(event, context)
