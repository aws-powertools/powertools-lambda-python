from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools import Logger

logger = Logger(service="order-processing")


@logger.inject_lambda_context
@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    # Set Logger on the context for automatic deduplication
    context.set_logger(logger)

    # Logs via context.logger appear only once, even during replays
    context.logger.info("Starting workflow", extra={"order_id": event.get("order_id")})

    result: str = context.step(
        lambda _: "processed",
        name="process_order",
    )

    # This log won't repeat when the function replays after completing the step above
    context.logger.info("Workflow completed", extra={"result": result})

    return result
