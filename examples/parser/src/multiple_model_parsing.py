from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field

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
    Union[Cat, Dog],
    Field(discriminator="animal"),
]


@event_parser(model=Animal)
def lambda_handler(event: Animal, _: Any) -> str:
    if isinstance(event, Cat):
        # we have a cat!
        return f"🐈: {event.name}"

    return f"🐶: {event.name}"
