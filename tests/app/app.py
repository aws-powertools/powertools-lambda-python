from typing import Dict

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import ApiGatewayResolver
from aws_lambda_powertools.event_handler.api_gateway import ProxyEventType
from aws_lambda_powertools.logging.correlation_paths import API_GATEWAY_HTTP
from aws_lambda_powertools.utilities.typing import LambdaContext

from .routers import health, items, users

tracer = Tracer()
logger = Logger()
app = ApiGatewayResolver(proxy_type=ProxyEventType.ALBEvent)
app.include_router(health.router, prefix="/health")
app.include_router(items.router)
app.include_router(users.router)


@logger.inject_lambda_context(correlation_id_path=API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
def handler(event: Dict, context: LambdaContext):
    app.resolve(event, context)
