from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext


class BasicModel(BaseModel):
    product: str
    version: str


@event_parser
def lambda_handler(event: BasicModel, context: LambdaContext):
    return {"product": event.product}
