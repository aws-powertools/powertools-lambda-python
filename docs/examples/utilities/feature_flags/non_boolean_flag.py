from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags

app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="features",
)

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event, context):
    # Get customer's tier from incoming request
    ctx = {"tier": event.get("tier", "standard")}

    # Evaluate `has_premium_features` base don customer's tier
    premium_features: list[str] = feature_flags.evaluate(
        name="premium_features",
        context=ctx,
        default=False,
    )
    for feature in premium_features:
        # enable premium features
        ...
