from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from aws_lambda_powertools.utilities.data_classes import (
    ALBEvent,
    APIGatewayProxyEvent,
    APIGatewayProxyEventV2,
    LambdaFunctionUrlEvent,
)
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext


class BaseRouter(ABC):
    current_event: BaseProxyEvent
    lambda_context: LambdaContext
    context: dict

    @abstractmethod
    def route(
        self,
        rule: str,
        method: Any,
        cors: Optional[bool] = None,
        compress: bool = False,
        cache_control: Optional[str] = None,
    ):
        raise NotImplementedError()

    def get(self, rule: str, cors: Optional[bool] = None, compress: bool = False, cache_control: Optional[str] = None):
        """Get route decorator with GET `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.get("/get-call")
        def simple_get():
            return {"message": "Foo"}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(rule, "GET", cors, compress, cache_control)

    def post(self, rule: str, cors: Optional[bool] = None, compress: bool = False, cache_control: Optional[str] = None):
        """Post route decorator with POST `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.post("/post-call")
        def simple_post():
            post_data: dict = app.current_event.json_body
            return {"message": post_data["value"]}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(rule, "POST", cors, compress, cache_control)

    def put(self, rule: str, cors: Optional[bool] = None, compress: bool = False, cache_control: Optional[str] = None):
        """Put route decorator with PUT `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.put("/put-call")
        def simple_put():
            put_data: dict = app.current_event.json_body
            return {"message": put_data["value"]}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(rule, "PUT", cors, compress, cache_control)

    def delete(
        self, rule: str, cors: Optional[bool] = None, compress: bool = False, cache_control: Optional[str] = None
    ):
        """Delete route decorator with DELETE `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.delete("/delete-call")
        def simple_delete():
            return {"message": "deleted"}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(rule, "DELETE", cors, compress, cache_control)

    def patch(
        self, rule: str, cors: Optional[bool] = None, compress: bool = False, cache_control: Optional[str] = None
    ):
        """Patch route decorator with PATCH `method`

        Examples
        --------
        Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

        ```python
        from aws_lambda_powertools import Tracer
        from aws_lambda_powertools.event_handler import APIGatewayRestResolver

        tracer = Tracer()
        app = APIGatewayRestResolver()

        @app.patch("/patch-call")
        def simple_patch():
            patch_data: dict = app.current_event.json_body
            patch_data["value"] = patched

            return {"message": patch_data}

        @tracer.capture_lambda_handler
        def lambda_handler(event, context):
            return app.resolve(event, context)
        ```
        """
        return self.route(rule, "PATCH", cors, compress, cache_control)

    def append_context(self, **additional_context):
        """Append key=value data as routing context"""
        self.context.update(**additional_context)

    def clear_context(self):
        """Resets routing context"""
        self.context.clear()


class Router(BaseRouter):
    """Router helper class to allow splitting ApiGatewayResolver into multiple files"""

    def __init__(self):
        self._routes: Dict[tuple, Callable] = {}
        self.api_resolver: Optional[BaseRouter] = None
        self.context = {}  # early init as customers might add context before event resolution

    def route(
        self,
        rule: str,
        method: Union[str, Union[List[str], Tuple[str]]],
        cors: Optional[bool] = None,
        compress: bool = False,
        cache_control: Optional[str] = None,
    ):
        def register_route(func: Callable):
            # Convert methods to tuple. It needs to be hashable as its part of the self._routes dict key
            methods = (method,) if isinstance(method, str) else tuple(method)
            self._routes[(rule, methods, cors, compress, cache_control)] = func
            return func

        return register_route


class APIGatewayRouter(Router):
    """Specialized Router class that exposes current_event as an APIGatewayProxyEvent"""

    current_event: APIGatewayProxyEvent


class APIGatewayHttpRouter(Router):
    """Specialized Router class that exposes current_event as an APIGatewayProxyEventV2"""

    current_event: APIGatewayProxyEventV2


class LambdaFunctionUrlRouter(Router):
    """Specialized Router class that exposes current_event as a LambdaFunctionUrlEvent"""

    current_event: LambdaFunctionUrlEvent


class ALBRouter(Router):
    """Specialized Router class that exposes current_event as an ALBEvent"""

    current_event: ALBEvent
