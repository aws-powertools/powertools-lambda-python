from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser import event_parser

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext


class BasicModel(BaseModel):
    product: str
    version: str


@event_parser
def lambda_handler(event: BasicModel, context: LambdaContext):
    return {"product": event.product}
