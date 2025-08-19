import os

import boto3

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
tracer = Tracer()
metrics = Metrics()
app = APIGatewayRestResolver()

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

table = dynamodb.Table(os.environ["TABLE_NAME"])
queue_url = os.environ["QUEUE_URL"]


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "powertools-cdk-api"}


@app.post("/tasks")
@tracer.capture_method
def create_task():
    task_data = app.current_event.json_body

    # Store in DynamoDB
    table.put_item(Item={"pk": task_data["task_id"], "task_type": task_data["task_type"], "status": "pending"})

    # Send to SQS for processing
    sqs.send_message(QueueUrl=queue_url, MessageBody=app.current_event.body)

    metrics.add_metric(name="TaskCreated", unit=MetricUnit.Count, value=1)
    logger.info("Task created", extra={"task_id": task_data["task_id"]})

    return {"message": "Task created successfully", "task_id": task_data["task_id"]}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    return app.resolve(event, context)
