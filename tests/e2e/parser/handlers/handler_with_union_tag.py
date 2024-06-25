from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext


class SuccessCallback(BaseModel):
    order_id: str
    status: Literal["success"]
    error_msg: str


class ErrorCallback(BaseModel):
    status: Literal["error"]
    error_msg: str


class PartialFailureCallback(BaseModel):
    status: Literal["partial"]
    error_msg: str


OrderCallback = Annotated[Union[SuccessCallback, ErrorCallback, PartialFailureCallback], Field(discriminator="status")]


@event_parser
def lambda_handler(event: OrderCallback, context: LambdaContext):
    return {"error_msg": event.error_msg}
