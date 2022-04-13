from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags

app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="features",
)

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event, context):
    apply_discount: bool = feature_flags.evaluate(
        name="ten_percent_off_campaign",
        default=False,
    )

    if apply_discount:
        # apply 10% discount to product
        ...
