from typing import Dict

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging.correlation_paths import APPLICATION_LOAD_BALANCER
from aws_lambda_powertools.utilities.typing import LambdaContext

from .routers import health, users

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()

app.include_router(health.router)
app.include_router(users.router)


@logger.inject_lambda_context(correlation_id_path=API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: Dict, context: LambdaContext):
    return app.resolve(event, context)
