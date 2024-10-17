import json
from typing import Any, Dict, Type, Union

from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.typing import LambdaContext

AnyInheritedModel = Union[Type[BaseModel], BaseModel]
RawDictOrModel = Union[Dict[str, Any], AnyInheritedModel]


class ModelWithUnionType(BaseModel):
    name: str
    profile: RawDictOrModel


def lambda_handler(event: ModelWithUnionType, context: LambdaContext):
    event = json.dumps(event)

    event_parsed = parse(event=event, model=ModelWithUnionType)

    return {"name": event_parsed.name}
