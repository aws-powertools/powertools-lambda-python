from dataclasses import dataclass

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext


@dataclass
class BasicDataclass:
    product: str
    version: str


@event_parser
def lambda_handler(event: BasicDataclass, context: LambdaContext):
    return {"product": event.product}
