import json
import re

import boto3
import custom_format_schema as schemas

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import SchemaValidationError, validate

# awsaccountid must have 12 digits
custom_format = {"awsaccountid": lambda value: re.match(r"^(\d{12})$", value)}


def lambda_handler(event, context: LambdaContext) -> dict:
    try:
        # validate input using custom json format
        validate(event=event, schema=schemas.INPUT, formats=custom_format)

        client_organization = boto3.client("organizations", region_name=event.get("region"))
        account_data = client_organization.describe_account(AccountId=event.get("accountid"))

        return {
            "account": json.dumps(account_data.get("Account"), default=str),
            "message": "Success",
            "statusCode": 200,
        }
    except SchemaValidationError as exception:
        return return_error_message(str(exception))
    except Exception as exception:
        return return_error_message(str(exception))


def return_error_message(message: str) -> dict:
    return {"account": None, "message": message, "statusCode": 400}
