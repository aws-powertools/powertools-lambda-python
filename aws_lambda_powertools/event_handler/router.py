from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.event_handler.api_gateway import Router

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.data_classes import (
        ALBEvent,
        APIGatewayProxyEvent,
        APIGatewayProxyEventV2,
        LambdaFunctionUrlEvent,
    )


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
