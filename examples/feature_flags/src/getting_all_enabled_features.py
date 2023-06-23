from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver()

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


@app.get("/products")
def list_products():
    # getting fields from request
    # https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/#accessing-request-details
    json_body = app.current_event.json_body
    headers = app.current_event.headers

    ctx = {**headers, **json_body}

    # getting price from payload
    price: float = float(json_body.get("price"))
    percent_discount: int = 0

    # all_features is evaluated to ["premium_features", "geo_customer_campaign", "ten_percent_off_campaign"]
    all_features: list[str] = feature_flags.get_enabled_features(context=ctx)

    if "geo_customer_campaign" in all_features:
        # apply 20% discounts for customers in NL
        percent_discount += 20

    if "ten_percent_off_campaign" in all_features:
        # apply additional 10% for all customers
        percent_discount += 10

    price = price * (100 - percent_discount) / 100

    return {"price": price}


def lambda_handler(event: dict, context: LambdaContext):
    return app.resolve(event, context)
