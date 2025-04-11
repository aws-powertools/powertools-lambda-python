from dataclasses import dataclass

from aws_lambda_powertools.utilities.data_masking import DataMasking

data_masker = DataMasking()


@dataclass
class User:
    name: str
    age: int


def lambda_handler(event, context):
    user = User(name="powertools", age=42)
    return data_masker.erase(user, fields=["age"])
