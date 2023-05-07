from typing import Any

from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext):
    """
    This feature flag is enabled under the following conditions:
    - The request payload contains a field 'tier' with the value 'premium'.

    Rule condition to be evaluated:
        "conditions": [
            {
                "action": "EQUALS",
                "key": "tier",
                "value": "premium"
            }
        ]
    """

    # Get customer's tier from incoming request
    ctx = {"tier": event.get("tier", "standard")}

    # Evaluate whether customer's tier has access to premium features
    # based on `has_premium_features` rules
    has_premium_features: Any = feature_flags.evaluate(name="premium_features", context=ctx, default=False)
    if has_premium_features:
        # enable premium features
        ...
