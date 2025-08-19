from __future__ import annotations

import json
import os
from typing import Any

import boto3

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()
metrics = Metrics()

# Initialize batch processor for SQS
processor = BatchProcessor(event_type=EventType.SQS)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


@tracer.capture_method
def record_handler(record):
    """Process individual SQS record"""
    try:
        # Parse message
        message_data = json.loads(record.body)
        task_id = message_data["task_id"]
        task_type = message_data["task_type"]

        logger.info("Processing task", extra={"task_id": task_id, "task_type": task_type})

        # Update task status in DynamoDB
        table.update_item(
            Key={"pk": task_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "processing"},
        )

        # Simulate work based on task type
        if task_type == "email":
            logger.info("Sending email", extra={"task_id": task_id})
        elif task_type == "report":
            logger.info("Generating report", extra={"task_id": task_id})
        else:
            logger.warning("Unknown task type", extra={"task_type": task_type})

        # Mark as completed
        table.update_item(
            Key={"pk": task_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": "completed"},
        )

        metrics.add_metric(name="TaskProcessed", unit="Count", value=1)
        metrics.add_metadata(key="task_type", value=task_type)

        return {"status": "success", "task_id": task_id}

    except Exception as e:
        logger.error("Task processing failed", extra={"error": str(e)})
        metrics.add_metric(name="TaskFailed", unit="Count", value=1)
        raise


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def lambda_handler(event: dict[str, Any], context: LambdaContext):
    """Process SQS messages using BatchProcessor"""

    return process_partial_response(
        event=event,
        record_handler=record_handler,
        processor=processor,
        context=context,
    )
