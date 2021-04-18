import base64
import json
import re
import zlib
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext


class ProxyEventType(Enum):
    http_api_v1 = "APIGatewayProxyEvent"
    http_api_v2 = "APIGatewayProxyEventV2"
    alb_event = "ALBEvent"
    api_gateway = http_api_v1


class Route:
    def __init__(
        self, method: str, rule: Any, func: Callable, cors: bool, compress: bool, cache_control: Optional[str]
    ):
        self.method = method.upper()
        self.rule = rule
        self.func = func
        self.cors = cors
        self.compress = compress
        self.cache_control = cache_control


class ApiGatewayResolver:
    current_event: BaseProxyEvent
    lambda_context: LambdaContext

    def __init__(self, proxy_type: Enum = ProxyEventType.http_api_v1):
        self._proxy_type = proxy_type
        self._routes: List[Route] = []

    def get(self, rule: str, cors: bool = False, compress: bool = False, cache_control: str = None):
        return self.route(rule, "GET", cors, compress, cache_control)

    def post(self, rule: str, cors: bool = False, compress: bool = False, cache_control: str = None):
        return self.route(rule, "POST", cors, compress, cache_control)

    def put(self, rule: str, cors: bool = False, compress: bool = False, cache_control: str = None):
        return self.route(rule, "PUT", cors, compress, cache_control)

    def delete(self, rule: str, cors: bool = False, compress: bool = False, cache_control: str = None):
        return self.route(rule, "DELETE", cors, compress, cache_control)

    def patch(self, rule: str, cors: bool = False, compress: bool = False, cache_control: str = None):
        return self.route(rule, "PATCH", cors, compress, cache_control)

    def route(self, rule: str, method: str, cors: bool = False, compress: bool = False, cache_control: str = None):
        def register_resolver(func: Callable):
            self._routes.append(Route(method, self._build_rule_pattern(rule), func, cors, compress, cache_control))
            return func

        return register_resolver

    def resolve(self, event, context) -> Dict[str, Any]:
        self.current_event = self._as_data_class(event)
        self.lambda_context = context
        route, args = self._find_route(self.current_event.http_method, self.current_event.path)
        result = route.func(**args)

        if isinstance(result, dict):
            status_code = 200
            content_type = "application/json"
            body: Union[str, bytes] = json.dumps(result)
        else:
            status_code, content_type, body = result
        headers = {"Content-Type": content_type}

        if route.cors:
            headers["Access-Control-Allow-Origin"] = "*"
            headers["Access-Control-Allow-Methods"] = route.method
            headers["Access-Control-Allow-Credentials"] = "true"

        if route.cache_control:
            headers["Cache-Control"] = route.cache_control if status_code == 200 else "no-cache"

        if route.compress and "gzip" in (self.current_event.get_header_value("accept-encoding") or ""):
            headers["Content-Encoding"] = "gzip"
            if isinstance(body, str):
                body = bytes(body, "utf-8")
            gzip = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
            body = gzip.compress(body) + gzip.flush()

        base64_encoded = False
        if isinstance(body, bytes):
            base64_encoded = True
            body = base64.b64encode(body).decode()

        return {"statusCode": status_code, "headers": headers, "body": body, "isBase64Encoded": base64_encoded}

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

    def _find_route(self, method: str, path: str) -> Tuple[Route, Dict]:
        method = method.upper()
        for route in self._routes:
            if method != route.method:
                continue
            match: Optional[re.Match] = route.rule.match(path)
            if match:
                return route, match.groupdict()

        raise ValueError(f"No route found for '{method}.{path}'")

    def __call__(self, event, context) -> Any:
        return self.resolve(event, context)
