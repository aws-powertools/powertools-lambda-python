from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools import Logger

logger = Logger(service="my-service")


@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    context.set_logger(logger)

    # Use context.logger for deduplication
    context.logger.info("Starting workflow")

    result: str = context.step(
        lambda _: "processed",
        name="process",
    )

    context.logger.info("Workflow completed")
    return result
