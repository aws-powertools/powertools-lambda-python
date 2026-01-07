from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics()


@metrics.log_metrics
@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    result: str = context.step(
        lambda _: "processed",
        name="process",
    )

    # Emit only at the end
    metrics.add_metric(name="WorkflowCompleted", unit=MetricUnit.Count, value=1)
    return result
