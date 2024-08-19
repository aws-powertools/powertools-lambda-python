from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="feature_flags",
    envelope="features",
)

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext):
    apply_discount: Any = feature_flags.evaluate(name="ten_percent_off_campaign", default=False)

    price: Any = event.get("price")

    if apply_discount:
        # apply 10% discount to product
        price = price * 0.9

    return {"price": price}
