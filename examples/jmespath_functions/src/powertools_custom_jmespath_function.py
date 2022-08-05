import base64

from jmespath.functions import signature

from aws_lambda_powertools.utilities.jmespath_utils import PowertoolsFunctions, extract_data_from_envelope


class CustomFunctions(PowertoolsFunctions):
    @signature({"types": ["string"]})  # Only decode if value is a string
    def _func_special_decoder(self, payload: str):
        payload_decode = base64.b64decode(payload)
        return payload_decode


custom_jmespath_options = {"custom_functions": CustomFunctions()}


def handler(event, context):
    # use the custom name after `_func_`
    extract_data_from_envelope(data=event, envelope="special_decoder(body)", jmespath_options=custom_jmespath_options)
    ...
