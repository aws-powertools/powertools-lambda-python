from typing import Any

from custom_s3_store_provider import S3StoreProvider

from aws_lambda_powertools.utilities.feature_flags import FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

s3_config_store = S3StoreProvider("your-bucket-name", "working_with_own_s3_store_provider_features.json")

feature_flags = FeatureFlags(store=s3_config_store)


def lambda_handler(event: dict, context: LambdaContext):
    apply_discount: Any = feature_flags.evaluate(name="ten_percent_off_campaign", default=False)

    price: Any = event.get("price")

    if apply_discount:
        # apply 10% discount to product
        price = price * 0.9

    return {"price": price}
