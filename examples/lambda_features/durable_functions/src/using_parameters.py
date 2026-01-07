from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]

from aws_lambda_powertools.utilities import parameters


def call_api(api_key: str) -> str:
    return f"called-with-{api_key[:4]}..."


@durable_execution
def handler(event: dict, context: DurableContext) -> str:
    # Parameters are fetched on each execution
    api_key = parameters.get_secret("api-key")

    result: str = context.step(
        lambda _: call_api(api_key),
        name="call_api",
    )

    return result
