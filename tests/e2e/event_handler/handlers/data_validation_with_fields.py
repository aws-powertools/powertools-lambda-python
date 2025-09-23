from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import Body

app = APIGatewayRestResolver(enable_validation=True)
app.enable_swagger()


class FooAction(BaseModel):
    action: Literal["foo"]
    foo_data: str


class BarAction(BaseModel):
    action: Literal["bar"]
    bar_data: int


Action = Annotated[FooAction | BarAction, Field(discriminator="action")]


@app.post("/data_validation_with_fields")
def create_action(action: Annotated[Action, Body(discriminator="action")]):
    return {"message": "Powertools e2e API"}


def lambda_handler(event, context):
    print(event)
    return app.resolve(event, context)
