from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags

app = APIGatewayRestResolver()

app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="features",
)
feature_flags = FeatureFlags(store=app_config)


@app.get("/products")
def list_products():
    ctx = {
        **app.current_event.headers,
        **app.current_event.json_body,
    }

    # all_features is evaluated to ["geo_customer_campaign", "ten_percent_off_campaign"]
    all_features: list[str] = feature_flags.get_enabled_features(context=ctx)

    if "geo_customer_campaign" in all_features:
        # apply discounts based on geo
        ...

    if "ten_percent_off_campaign" in all_features:
        # apply additional 10% for all customers
        ...


def lambda_handler(event, context):
    return app.resolve(event, context)
