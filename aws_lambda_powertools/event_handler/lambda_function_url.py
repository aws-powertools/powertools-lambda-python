from typing import Callable, Dict, List, Optional

from aws_lambda_powertools.event_handler import CORSConfig
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, ProxyEventType
from aws_lambda_powertools.utilities.data_classes import LambdaFunctionUrlEvent


class LambdaFunctionUrlResolver(ApiGatewayResolver):
    current_event: LambdaFunctionUrlEvent

    def __init__(
        self,
        cors: Optional[CORSConfig] = None,
        debug: Optional[bool] = None,
        serializer: Optional[Callable[[Dict], str]] = None,
        strip_prefixes: Optional[List[str]] = None,
    ):
        super().__init__(ProxyEventType.LambdaFunctionUrlEvent, cors, debug, serializer, strip_prefixes)
