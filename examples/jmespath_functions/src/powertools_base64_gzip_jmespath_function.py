import base64
import binascii
import gzip
import json

import powertools_base64_gzip_jmespath_schema as schemas
from jmespath.exceptions import JMESPathTypeError

from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import SchemaValidationError, validate


def lambda_handler(event, context: LambdaContext) -> dict:

    # Try to validate the schema
    try:
        validate(event=event, schema=schemas.INPUT, envelope="powertools_base64_gzip(payload) | powertools_json(@)")

        encoded_payload = base64.b64decode(event["payload"])
        uncompressed_payload = gzip.decompress(encoded_payload).decode()

        logs = process_cloudwatch_logs(json.loads(uncompressed_payload))
        return {
            "message": logs,
            "success": True,
        }

    except JMESPathTypeError:
        return return_error_message("The powertools_base64_gzip() envelope function must match a valid path.")
    except binascii.Error:
        return return_error_message("Payload must be valid base64 encoded string")
    except json.JSONDecodeError:
        return return_error_message("Payload must be valid JSON (base64 encoded).")
    except SchemaValidationError as exception:
        # if validation fails, a SchemaValidationError will be raised with the wrong fields
        return return_error_message(str(exception))


def return_error_message(message: str) -> dict:
    return {"message": message, "success": False}


def process_cloudwatch_logs(event: dict) -> str:
    owner = event.get("owner")  # noqa F841
    log_group = event.get("logGroup")  # noqa F841
    # Add your logic here
    ...
    return "Logs processed"
