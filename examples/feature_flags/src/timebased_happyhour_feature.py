from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event, context):
    is_happy_hour = feature_flags.evaluate(name="happy_hour", default=False)

    if is_happy_hour:
        # Apply special discount
        pass
