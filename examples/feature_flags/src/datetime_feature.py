from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext):
    """
    This feature flag is enabled under the following conditions:
    - Start date: December 25th, 2022 at 12:00:00 PM EST
    - End date: December 31st, 2022 at 11:59:59 PM EST
    - Timezone: America/New_York

    Rule condition to be evaluated:
        "conditions": [
          {
            "action": "SCHEDULE_BETWEEN_DATETIME_RANGE",
            "key": "CURRENT_DATETIME",
            "value": {
              "START": "2022-12-25T12:00:00",
              "END": "2022-12-31T23:59:59",
              "TIMEZONE": "America/New_York"
            }
          }
        ]
    """

    # Checking if the Christmas discount is enable
    xmas_discount = feature_flags.evaluate(name="christmas_discount", default=False)

    if xmas_discount:
        # Enable special discount on christmas:
        return {"message": "The Christmas discount is enabled."}

    return {"message": "The Christmas discount is not enabled."}
