from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from aws_lambda_powertools.utilities.parser import event_parser


class Cat(BaseModel):
    animal: Literal["cat"]
    name: str
    meow: int


class Dog(BaseModel):
    animal: Literal["dog"]
    name: str
    bark: int


Animal = Annotated[
    Cat | Dog,
    Field(discriminator="animal"),
]


@event_parser(model=Animal)
def lambda_handler(event: Animal, _: Any) -> str:
    if isinstance(event, Cat):
        # we have a cat!
        return f"🐈: {event.name}"

    return f"🐶: {event.name}"
