from typing import Any

from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

app_config = AppConfigStore(environment="dev", application="comments", name="config")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext):
    # Get customer's tier from incoming request
    ctx = {"tier": event.get("tier", "standard")}

    # Evaluate `has_premium_features` based on customer's tier
    premium_features: Any = feature_flags.evaluate(name="premium_features", context=ctx, default=[])

    return {"Premium features enabled": premium_features}
