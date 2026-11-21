from typing import Any

from aws_lambda_powertools.utilities.feature_flags import AppConfigExtensionStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

# Fetch feature flags from the AWS AppConfig Agent Lambda extension instead of calling AppConfig with boto3
app_config = AppConfigExtensionStore(
    environment="dev",
    application="product-catalogue",
    name="features",
)

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext) -> dict[str, Any]:
    ctx = {"tenant_id": "ABC", "username": "lessa"}

    has_premium_features: Any = feature_flags.evaluate(name="premium_features", context=ctx, default=False)

    return {"statusCode": 200, "body": {"premium_features": has_premium_features}}
