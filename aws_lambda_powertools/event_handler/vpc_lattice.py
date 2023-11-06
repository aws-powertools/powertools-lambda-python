from typing import Callable, Dict, List, Optional, Pattern, Union

from aws_lambda_powertools.event_handler import CORSConfig
from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    ProxyEventType,
)
from aws_lambda_powertools.utilities.data_classes import VPCLatticeEvent, VPCLatticeEventV2


class VPCLatticeResolver(ApiGatewayResolver):
    """VPC Lattice resolver

    Documentation:
    - https://docs.aws.amazon.com/lambda/latest/dg/services-vpc-lattice.html
    - https://docs.aws.amazon.com/lambda/latest/dg/services-vpc-lattice.html#vpc-lattice-receiving-events

    Examples
    --------
    Simple example integrating with Tracer

    ```python
    from aws_lambda_powertools import Tracer
    from aws_lambda_powertools.event_handler import VPCLatticeResolver

    tracer = Tracer()
    app = VPCLatticeResolver()

    @app.get("/get-call")
    def simple_get():
        return {"message": "Foo"}

    @app.post("/post-call")
    def simple_post():
        post_data: dict = app.current_event.json_body
        return {"message": post_data}

    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    """

    current_event: VPCLatticeEvent

    def __init__(
        self,
        cors: Optional[CORSConfig] = None,
        debug: Optional[bool] = None,
        serializer: Optional[Callable[[Dict], str]] = None,
        strip_prefixes: Optional[List[Union[str, Pattern]]] = None,
        enable_validation: bool = False,
    ):
        """Amazon VPC Lattice resolver"""
        super().__init__(ProxyEventType.VPCLatticeEvent, cors, debug, serializer, strip_prefixes, enable_validation)

    def _get_base_path(self) -> str:
        return ""


class VPCLatticeV2Resolver(ApiGatewayResolver):
    """VPC Lattice resolver

    Documentation:
    - https://docs.aws.amazon.com/lambda/latest/dg/services-vpc-lattice.html
    - https://docs.aws.amazon.com/lambda/latest/dg/services-vpc-lattice.html#vpc-lattice-receiving-events

    Examples
    --------
    Simple example integrating with Tracer

    ```python
    from aws_lambda_powertools import Tracer
    from aws_lambda_powertools.event_handler import VPCLatticeV2Resolver

    tracer = Tracer()
    app = VPCLatticeV2Resolver()

    @app.get("/get-call")
    def simple_get():
        return {"message": "Foo"}

    @app.post("/post-call")
    def simple_post():
        post_data: dict = app.current_event.json_body
        return {"message": post_data}

    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    """

    current_event: VPCLatticeEventV2

    def __init__(
        self,
        cors: Optional[CORSConfig] = None,
        debug: Optional[bool] = None,
        serializer: Optional[Callable[[Dict], str]] = None,
        strip_prefixes: Optional[List[Union[str, Pattern]]] = None,
        enable_validation: bool = False,
    ):
        """Amazon VPC Lattice resolver"""
        super().__init__(ProxyEventType.VPCLatticeEventV2, cors, debug, serializer, strip_prefixes, enable_validation)

    def _get_base_path(self) -> str:
        return ""
