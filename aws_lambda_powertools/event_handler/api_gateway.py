import base64
import json
import re
import zlib
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from aws_lambda_powertools.shared.json_encoder import Encoder
from aws_lambda_powertools.utilities.data_classes import ALBEvent, APIGatewayProxyEvent, APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext


class ProxyEventType(Enum):
    http_api_v1 = "APIGatewayProxyEvent"
    http_api_v2 = "APIGatewayProxyEventV2"
    alb_event = "ALBEvent"
    api_gateway = http_api_v1


class CORSConfig(object):
    _REQUIRED_HEADERS = ["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", "X-Amz-Security-Token"]

    def __init__(
        self,
        allow_origin: str = "*",
        allow_headers: List[str] = None,
        expose_headers: List[str] = None,
        max_age: int = None,
        allow_credentials: bool = False,
    ):
        self.allow_origin = allow_origin
        self.allow_headers = set((allow_headers or []) + self._REQUIRED_HEADERS)
        self.expose_headers = expose_headers or []
        self.max_age = max_age
        self.allow_credentials = allow_credentials

    def to_dict(self) -> Dict[str, str]:
        headers = {
            "Access-Control-Allow-Origin": self.allow_origin,
            "Access-Control-Allow-Headers": ",".join(sorted(self.allow_headers)),
        }
        if self.expose_headers:
            headers["Access-Control-Expose-Headers"] = ",".join(self.expose_headers)
        if self.max_age is not None:
            headers["Access-Control-Max-Age"] = str(self.max_age)
        if self.allow_credentials is True:
            headers["Access-Control-Allow-Credentials"] = "true"
        return headers


class Route:
    def __init__(
        self,
        method: str,
        rule: Any,
        func: Callable,
        cors: Union[bool, CORSConfig],
        compress: bool,
        cache_control: Optional[str],
    ):
        self.method = method.upper()
        self.rule = rule
        self.func = func
        self.cors: Optional[CORSConfig]
        if cors is True:
            self.cors = CORSConfig()
        elif isinstance(cors, CORSConfig):
            self.cors = cors
        else:
            self.cors = None
        self.compress = compress
        self.cache_control = cache_control


class Response:
    def __init__(
        self, status_code: int, content_type: Optional[str], body: Union[str, bytes, None], headers: Dict = None
    ):
        self.status_code = status_code
        self.body = body
        self.base64_encoded = False
        self.headers: Dict = headers or {}
        if content_type:
            self.headers.setdefault("Content-Type", content_type)

    def add_cors(self, cors: CORSConfig):
        self.headers.update(cors.to_dict())

    def add_cache_control(self, cache_control: str):
        self.headers["Cache-Control"] = cache_control if self.status_code == 200 else "no-cache"

    def compress(self):
        self.headers["Content-Encoding"] = "gzip"
        if isinstance(self.body, str):
            self.body = bytes(self.body, "utf-8")
        gzip = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
        self.body = gzip.compress(self.body) + gzip.flush()

    def to_dict(self) -> Dict[str, Any]:
        result = {"statusCode": self.status_code, "headers": self.headers}
        if isinstance(self.body, bytes):
            self.base64_encoded = True
            self.body = base64.b64encode(self.body).decode()
        if self.body:
            result["isBase64Encoded"] = self.base64_encoded
            result["body"] = self.body
        return result


class ApiGatewayResolver:
    current_event: BaseProxyEvent
    lambda_context: LambdaContext

    def __init__(self, proxy_type: Enum = ProxyEventType.http_api_v1):
        self._proxy_type = proxy_type
        self._routes: List[Route] = []
        self._cors: Optional[CORSConfig] = None
        self._cors_methods: Set[str] = set()

    def get(self, rule: str, cors: Union[bool, CORSConfig] = False, compress: bool = False, cache_control: str = None):
        return self.route(rule, "GET", cors, compress, cache_control)

    def post(self, rule: str, cors: Union[bool, CORSConfig] = False, compress: bool = False, cache_control: str = None):
        return self.route(rule, "POST", cors, compress, cache_control)

    def put(self, rule: str, cors: Union[bool, CORSConfig] = False, compress: bool = False, cache_control: str = None):
        return self.route(rule, "PUT", cors, compress, cache_control)

    def delete(
        self, rule: str, cors: Union[bool, CORSConfig] = False, compress: bool = False, cache_control: str = None
    ):
        return self.route(rule, "DELETE", cors, compress, cache_control)

    def patch(
        self, rule: str, cors: Union[bool, CORSConfig] = False, compress: bool = False, cache_control: str = None
    ):
        return self.route(rule, "PATCH", cors, compress, cache_control)

    def route(
        self,
        rule: str,
        method: str,
        cors: Union[bool, CORSConfig] = False,
        compress: bool = False,
        cache_control: str = None,
    ):
        def register_resolver(func: Callable):
            route = Route(method, self._compile_regex(rule), func, cors, compress, cache_control)
            self._routes.append(route)
            if route.cors:
                if self._cors is None:
                    self._cors = route.cors
                self._cors_methods.add(route.method)
            return func

        return register_resolver

    def resolve(self, event, context) -> Dict[str, Any]:
        self.current_event = self._to_data_class(event)
        self.lambda_context = context
        route, args = self._find_route(self.current_event.http_method.upper(), self.current_event.path)
        response = self.to_response(route.func(**args))

        if route.cors:
            response.add_cors(route.cors)
        if route.cache_control:
            response.add_cache_control(route.cache_control)
        if route.compress and "gzip" in (self.current_event.get_header_value("accept-encoding") or ""):
            response.compress()

        return response.to_dict()

    @staticmethod
    def to_response(result: Union[Tuple[int, str, Union[bytes, str]], Dict, Response]) -> Response:
        if isinstance(result, Response):
            return result
        elif isinstance(result, dict):
            return Response(
                status_code=200,
                content_type="application/json",
                body=json.dumps(result, separators=(",", ":"), cls=Encoder),
            )
        else:  # Tuple[int, str, Union[bytes, str]]
            return Response(*result)

    @staticmethod
    def _compile_regex(rule: str):
        rule_regex: str = re.sub(r"(<\w+>)", r"(?P\1.+)", rule)
        return re.compile("^{}$".format(rule_regex))

    def _to_data_class(self, event: Dict) -> BaseProxyEvent:
        if self._proxy_type == ProxyEventType.http_api_v1:
            return APIGatewayProxyEvent(event)
        if self._proxy_type == ProxyEventType.http_api_v2:
            return APIGatewayProxyEventV2(event)
        return ALBEvent(event)

    @staticmethod
    def _preflight(allowed_methods: Set):
        allowed_methods.add("OPTIONS")
        headers = {"Access-Control-Allow-Methods": ",".join(sorted(allowed_methods))}
        return Response(204, None, None, headers)

    def _find_route(self, method: str, path: str) -> Tuple[Route, Dict]:
        for route in self._routes:
            if method != route.method:
                continue
            match: Optional[re.Match] = route.rule.match(path)
            if match:
                return route, match.groupdict()

        if method == "OPTIONS" and self._cors is not None:
            # Most be the preflight options call
            return (
                Route("OPTIONS", None, self._preflight, self._cors, False, None),
                {"allowed_methods": self._cors_methods},
            )

        raise ValueError(f"No route found for '{method}.{path}'")

    def __call__(self, event, context) -> Any:
        return self.resolve(event, context)
