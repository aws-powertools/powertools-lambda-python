from typing import List

from pydantic import BaseModel, Field

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
# Enable validation globally
app = APIGatewayRestResolver(enable_validation=True)


class Task(BaseModel):
    """Task model with validation"""

    id: int = Field(ge=1, description="Task ID must be positive")
    title: str = Field(min_length=1, max_length=100, description="Task title")
    completed: bool = Field(default=False, description="Task completion status")


class LegacyResponse(BaseModel):
    """Response model used by legacy endpoints"""

    status: str
    data: dict


@app.get("/tasks/<task_id>")
def get_task(task_id: int) -> Task:
    """
    This route inherits global validation (enable_validation=True from resolver).
    Request and response will be validated against OpenAPI schema.
    """
    logger.info(f"Getting task {task_id}")
    return Task(id=task_id, title="Sample Task", completed=False)


@app.post("/tasks")
def create_task(task: Task) -> Task:
    """
    This route also inherits global validation.
    Request body will be validated and parsed into Task model.
    """
    logger.info(f"Creating task: {task.title}")
    return task


@app.get("/legacy/status", enable_validation=False)
def legacy_status_check():
    """
    This route explicitly disables validation even though resolver has it enabled.
    Useful for legacy endpoints that don't conform to your OpenAPI schema yet.

    The response can be any dict - no validation will occur.
    """
    logger.info("Legacy status check - no validation")
    # This response doesn't match any model - that's OK with validation disabled
    return {
        "status": "ok",
        "timestamp": "2024-01-01",
        "extra_field": "not in schema",
        "nested": {"arbitrary": "data"},
    }


@app.get("/legacy/info", enable_validation=False)
def legacy_info() -> dict:
    """
    Another legacy endpoint with validation disabled.
    Can return arbitrary structure without validation.
    """
    return {
        "version": "1.0",
        "mode": "legacy",
        "features": ["one", "two", "three"],
    }


@app.get("/tasks")
def list_tasks() -> List[Task]:
    """
    This route has validation enabled (inherited from resolver).
    Response will be validated to ensure it's a list of Task objects.
    """
    logger.info("Listing all tasks")
    return [
        Task(id=1, title="First Task", completed=True),
        Task(id=2, title="Second Task", completed=False),
    ]


@app.delete("/tasks/<task_id>", enable_validation=False)
def delete_task(task_id: str):
    """
    Validation disabled for this endpoint - maybe it's being migrated.
    Notice task_id is a str here (not int) - validation would normally catch this.
    """
    logger.info(f"Deleting task (no validation): {task_id}")
    return {"message": f"Task {task_id} deleted"}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)


"""
Benefits of per-route validation:

1. **Gradual Migration**: Enable validation globally, then disable it for legacy routes
   that need more time to be updated.

2. **Mixed Workloads**: Validate critical business logic endpoints while allowing
   flexibility for internal/admin endpoints.

3. **Performance**: Disable validation for high-throughput endpoints where you trust
   the input and want to minimize overhead.

4. **Development**: Enable validation for new features while keeping old code working.

Example requests:

# Validated endpoint (will check task_id is int, response matches Task model)
GET /tasks/123

# Legacy endpoint (no validation, returns any structure)
GET /legacy/status

# Validated POST (request body must match Task model)
POST /tasks
{"id": 1, "title": "New Task", "completed": false}

# Legacy delete (no validation, task_id can be any string)
DELETE /tasks/abc123
"""
