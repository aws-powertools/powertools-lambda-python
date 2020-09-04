import json

import jmespath


class PowertoolsJson(jmespath.functions.Functions):
    @jmespath.functions.signature({"types": ["string"]})
    def _func_powertools_json(self, value):
        return json.loads(value)
