from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@logger.inject_lambda_context(correlation_id_path="headers.my_request_id_header")
def lambda_handler(event: dict, context: LambdaContext) -> str:
    logger.debug(f"Correlation ID => {logger.get_correlation_id()}")
    logger.info("Collecting payment")

    return "hello world"
