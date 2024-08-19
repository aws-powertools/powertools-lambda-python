from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def lambda_handler(event: dict, context: LambdaContext) -> str:
    logger.append_keys(sample_key="value")
    logger.info("Collecting payment")

    logger.remove_keys(["sample_key"])
    logger.info("Collecting payment without sample key")

    return "hello world"
