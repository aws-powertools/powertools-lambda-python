from pydantic import BaseModel

from aws_lambda_powertools.utilities.data_masking import DataMasking

data_masker = DataMasking()


class User(BaseModel):
    name: str
    age: int


def lambda_handler(event, context):
    user = User(name="powertools", age=42)
    return data_masker.erase(user, fields=["age"])
