from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event, context):
    # Get customer's tier from incoming request
    ctx = {"tier": event.get("tier", "standard")}

    weekend_premium_discount = feature_flags.evaluate(name="weekend_premium_discount", default=False, context=ctx)

    if weekend_premium_discount:
        # Enable special discount for premium members on weekends
        pass
