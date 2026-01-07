from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
metrics = Metrics()


@metrics.log_metrics
@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    context.set_logger(logger)

    result: str = context.step(
        lambda _: "processed",
        name="process_order",
    )

    # Emit metrics only at workflow completion to avoid duplicates
    metrics.add_metric(name="WorkflowCompleted", unit=MetricUnit.Count, value=1)

    return result
