from __future__ import annotations

from typing import TYPE_CHECKING

from tracer_reuse_module import collect_payment

from aws_lambda_powertools import Tracer

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> str:
    charge_id = event.get("charge_id", "")
    return collect_payment(charge_id=charge_id)
