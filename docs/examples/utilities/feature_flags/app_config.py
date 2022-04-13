import jmespath
from botocore.config import Config

from aws_lambda_powertools.utilities.feature_flags import AppConfigStore

boto_config = Config(read_timeout=10, retries={"total_max_attempts": 2})

# Custom JMESPath functions
class CustomFunctions(jmespath.functions.Functions):
    @jmespath.functions.signature({"types": ["string"]})
    def _func_special_decoder(self, s):
        return my_custom_decoder_logic(s)


custom_jmespath_options = {"custom_functions": CustomFunctions()}

app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="configuration",
    max_age=120,
    envelope="features",
    sdk_config=boto_config,
    jmespath_options=custom_jmespath_options,
)
