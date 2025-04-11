from pydantic import BaseModel

from aws_lambda_powertools.utilities.data_masking import DataMasking


class User(BaseModel):
    name: str
    age: int


def lambda_handler(event, context):
    # Create a sample User instance
    user = User(name="powertools", age=42)
    # Erase the 'age' field
    masked = DataMasking().erase(user, fields=["age"])
    return masked
