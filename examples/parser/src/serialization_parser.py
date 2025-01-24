from pydantic import BaseModel

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


class UserModel(BaseModel):
    username: str
    parentid_1: str
    parentid_2: str


def validate_user(event):
    try:
        user = parse(model=UserModel, event=event)
        return {"statusCode": 200, "body": user.model_dump_json()}
    except Exception as e:
        logger.exception("Validation error")
        return {"statusCode": 400, "body": str(e)}


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info("Received event", extra={"event": event})

    result = validate_user(event)

    if result["statusCode"] == 200:
        user = UserModel.model_validate_json(result["body"])
        logger.info("User validated successfully", extra={"username": user.username})

        # Example of serialization
        user_dict = user.model_dump()
        user_json = user.model_dump_json()

        logger.debug("User serializations", extra={"dict": user_dict, "json": user_json})

    return result
