from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags

app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="configuration",
    envelope="feature_flags",
)

feature_flags = FeatureFlags(store=app_config)

config = app_config.get_raw_configuration
...
