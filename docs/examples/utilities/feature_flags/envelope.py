from aws_lambda_powertools.utilities.feature_flags import AppConfigStore

app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="configuration",
    envelope="feature_flags",
)
