from typing import Dict

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import ApiGatewayResolver
from aws_lambda_powertools.event_handler.api_gateway import ProxyEventType
from aws_lambda_powertools.utilities.typing import LambdaContext

from .routers import health

tracer = Tracer()
logger = Logger()
app = ApiGatewayResolver(proxy_type=ProxyEventType.ALBEvent)
app.include_router(health.router, prefix="/health")


@tracer.capture_lambda_handler
def handler(event: Dict, context: LambdaContext):
    app.resolve(event, context)
