from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools import Logger

logger = Logger(service="order-processing")


@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    # Set Powertools Logger on the context
    context.set_logger(logger)

    # Now context.logger uses Powertools with automatic enrichment and deduplication
    context.logger.info("Starting workflow", extra={"order_id": event.get("order_id")})

    result: str = context.step(
        lambda _: "processed",
        name="process_order",
    )

    context.logger.info("Workflow completed", extra={"result": result})
    return result
