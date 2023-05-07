from typing import Any

from botocore.config import Config
from jmespath.functions import Functions, signature

from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

boto_config = Config(read_timeout=10, retries={"total_max_attempts": 2})


# Custom JMESPath functions
class CustomFunctions(Functions):
    @signature({"types": ["object"]})
    def _func_special_decoder(self, features):
        # You can add some logic here
        return features


custom_jmespath_options = {"custom_functions": CustomFunctions()}


app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="features",
    max_age=120,
    envelope="special_decoder(features)",  # using a custom function defined in CustomFunctions Class
    sdk_config=boto_config,
    jmespath_options=custom_jmespath_options,
)

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext):
    apply_discount: Any = feature_flags.evaluate(name="ten_percent_off_campaign", default=False)

    price: Any = event.get("price")

    if apply_discount:
        # apply 10% discount to product
        price = price * 0.9

    return {"price": price}
