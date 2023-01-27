from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event, context):
    # Get customer's tier from incoming request
    xmas_discount = feature_flags.evaluate(name="christmas_discount", default=False)

    if xmas_discount:
        # Enable special discount on christmas:
        pass
