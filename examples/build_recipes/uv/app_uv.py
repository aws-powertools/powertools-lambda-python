from __future__ import annotations

from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()
metrics = Metrics()
app = APIGatewayRestResolver()


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "lambda-powertools-uv"}


@app.get("/metrics")
def get_metrics():
    metrics.add_metric(name="MetricsEndpointCalled", unit="Count", value=1)
    return {"message": "Metrics recorded"}


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def lambda_handler(event: dict[str, Any], context: LambdaContext):
    return app.resolve(event, context)
