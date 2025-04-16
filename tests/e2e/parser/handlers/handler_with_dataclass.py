from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.parser import event_parser

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext


@dataclass
class BasicDataclass:
    product: str
    version: str


@event_parser
def lambda_handler(event: BasicDataclass, context: LambdaContext):
    return {"product": event.product}
