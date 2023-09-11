import base64
import binascii
import zlib

from jmespath.exceptions import JMESPathTypeError
from jmespath.functions import signature

from aws_lambda_powertools.utilities.jmespath_utils import (
    PowertoolsFunctions,
    extract_data_from_envelope,
)


class CustomFunctions(PowertoolsFunctions):
    # only decode if value is a string
    # see supported data types: https://jmespath.org/specification.html#built-in-functions
    @signature({"types": ["string"]})
    def _func_decode_zlib_compression(self, payload: str):
        decoded: bytes = base64.b64decode(payload)
        return zlib.decompress(decoded)


custom_jmespath_options = {"custom_functions": CustomFunctions()}


def lambda_handler(event, context) -> dict:
    try:
        logs = []
        logs.append(
            extract_data_from_envelope(
                data=event,
                # NOTE: Use the prefix `_func_` before the name of the function
                envelope="Records[*].decode_zlib_compression(log)",
                jmespath_options=custom_jmespath_options,
            ),
        )
        return {"logs": logs, "message": "Extracted messages", "success": True}
    except JMESPathTypeError:
        return return_error_message("The envelope function must match a valid path.")
    except zlib.error:
        return return_error_message("Log must be a valid zlib compressed message")
    except binascii.Error:
        return return_error_message("Log must be a valid base64 encoded string")


def return_error_message(message: str) -> dict:
    return {"logs": None, "message": message, "success": False}
