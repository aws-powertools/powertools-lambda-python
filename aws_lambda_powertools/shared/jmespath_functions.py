import base64
import gzip
import json

import jmespath


class PowertoolsFunctions(jmespath.functions.Functions):
    @jmespath.functions.signature({"types": ["string"]})
    def _func_powertools_json(self, value):
        return json.loads(value)

    @jmespath.functions.signature({"types": ["string"]})
    def _func_powertools_base64(self, value):
        return base64.b64decode(value).decode()

    @jmespath.functions.signature({"types": ["string"]})
    def _func_powertools_base64_gzip(self, value):
        encoded = base64.b64decode(value)
        uncompressed = gzip.decompress(encoded)

        return uncompressed.decode()
