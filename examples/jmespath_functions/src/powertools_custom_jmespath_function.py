import base64
import binascii

import snappy
from jmespath.exceptions import JMESPathTypeError
from jmespath.functions import signature

from aws_lambda_powertools.utilities.jmespath_utils import PowertoolsFunctions, extract_data_from_envelope


class CustomFunctions(PowertoolsFunctions):
    # only decode if value is a string
    # see supported data types: https://jmespath.org/specification.html#built-in-functions
    @signature({"types": ["string"]})
    def _func_decode_snappy_compression(self, payload: str):
        decoded = base64.b64decode(payload)
        # uncompressing snappy messages - very common compression in Kafka
        uncompressed = snappy.uncompress(decoded)
        return uncompressed


custom_jmespath_options = {"custom_functions": CustomFunctions()}


def lambda_handler(event, context) -> dict:

    try:
        logs: list = []
        # use the prefix `_func_` before the name of the function
        logs.append(
            extract_data_from_envelope(
                data=event,
                envelope="Records[*].decode_snappy_compression(log)",
                jmespath_options=custom_jmespath_options,
            )
        )
        return {"logs": logs, "message": "Extracted messages", "success": True}
    except JMESPathTypeError:
        return return_error_message("The envelope function must match a valid path.")
    except snappy.UncompressError:
        return return_error_message("Log must be valid snappy compressed binary")
    except binascii.Error:
        return return_error_message("Log must be valid base64 encoded string")


def return_error_message(message: str) -> dict:
    return {"logs": None, "message": message, "success": False}
