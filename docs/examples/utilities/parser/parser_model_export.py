from aws_lambda_powertools.utilities import Logger
from aws_lambda_powertools.utilities.parser import BaseModel, ValidationError, parse, validator

logger = Logger(service="user")


class UserModel(BaseModel):
    username: str
    password1: str
    password2: str


payload = {
    "username": "universe",
    "password1": "myp@ssword",
    "password2": "repeat password",
}


def my_function():
    try:
        return parse(model=UserModel, event=payload)
    except ValidationError as e:
        logger.exception(e.json())
        return {"status_code": 400, "message": "Invalid username"}


User: UserModel = my_function()
user_dict = User.dict()
user_json = User.json()
user_json_schema_as_dict = User.schema()
user_json_schema_as_json = User.schema_json(indent=2)
