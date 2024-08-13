from __future__ import annotations

from typing import TYPE_CHECKING

from logger_reuse_payment import inject_payment_id

from aws_lambda_powertools import Logger

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> str:
    inject_payment_id(context=event)
    logger.info("Collecting payment")
    return "hello world"
