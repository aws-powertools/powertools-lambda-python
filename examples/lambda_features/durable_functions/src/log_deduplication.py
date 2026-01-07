from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools import Logger

logger = Logger(service="order-processing")


@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    context.set_logger(logger)

    # This log appears only once, even if the function is replayed
    context.logger.info("Starting workflow")

    result1: str = context.step(lambda _: "step1-done", name="step_1")
    context.logger.info("Step 1 completed")  # Only once

    result2: str = context.step(lambda _: "step2-done", name="step_2")
    context.logger.info("Step 2 completed")  # Only once

    return f"{result1}-{result2}"
