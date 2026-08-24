import requests
from pydantic import BaseModel

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
tracer = Tracer()
metrics = Metrics()
app = APIGatewayRestResolver()


class UserModel(BaseModel):
    name: str
    email: str
    age: int | None = None


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "powertools-sam-layers"}


@app.post("/users")
def create_user(user: UserModel):
    logger.info("Creating user", extra={"user": user.model_dump()})
    metrics.add_metric(name="UserCreated", unit=MetricUnit.Count, value=1)
    return {"message": f"User {user.name} created successfully"}


@app.get("/external")
@tracer.capture_method
def fetch_external_data():
    """Example using requests from dependencies layer"""
    response = requests.get("https://httpbin.org/json")
    data = response.json()

    metrics.add_metric(name="ExternalApiCalled", unit=MetricUnit.Count, value=1)
    return {"external_data": data}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    return app.resolve(event, context)
