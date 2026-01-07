from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools import Logger, Tracer

tracer = Tracer()
logger = Logger()


@tracer.capture_lambda_handler
@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    context.set_logger(logger)

    result: str = context.step(
        lambda _: process_data(),
        name="process_data",
    )

    return result


@tracer.capture_method
def process_data() -> str:
    # This is traced on first execution
    # On replay, the cached result is used
    return "processed"
