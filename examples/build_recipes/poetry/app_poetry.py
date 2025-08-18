from typing import Optional

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
    age: Optional[int] = None


@app.post("/users")
def create_user(user: UserModel):
    logger.info("Creating user", extra={"user": user.model_dump()})
    metrics.add_metric(name="UserCreated", unit=MetricUnit.Count, value=1)
    return {"message": f"User {user.name} created successfully", "user": user.model_dump()}


@app.get("/users")
def list_users():
    logger.info("Listing users")
    metrics.add_metric(name="UsersListed", unit=MetricUnit.Count, value=1)
    return {"users": [{"name": "John Doe", "email": "john@example.com", "age": 30}]}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    return app.resolve(event, context)
