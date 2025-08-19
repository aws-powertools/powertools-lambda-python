from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
tracer = Tracer()
metrics = Metrics()
app = APIGatewayRestResolver()


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "powertools-cdk"}


@app.get("/metrics")
def get_metrics():
    metrics.add_metric(name="MetricsEndpointCalled", unit=MetricUnit.Count, value=1)
    return {"message": "Metrics recorded"}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    return app.resolve(event, context)
