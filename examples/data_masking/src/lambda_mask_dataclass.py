from dataclasses import dataclass
from aws_lambda_powertools.utilities.data_masking import DataMasking

@dataclass
class User:
    name: str
    age: int

def lambda_handler(event, context):
    user = User(name="powertools", age=42)
    masked = DataMasking().erase(user, fields=["age"])
    return masked