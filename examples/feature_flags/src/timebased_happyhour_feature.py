from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext):
    """
    This feature flag is enabled under the following conditions:
    - Every day between 17:00 to 19:00 in Europe/Copenhagen timezone

    Rule condition to be evaluated:
        "conditions": [
          {
            "action": "SCHEDULE_BETWEEN_TIME_RANGE",
            "key": "CURRENT_TIME",
            "value": {
              "START": "17:00",
              "END": "19:00",
              "TIMEZONE": "Europe/Copenhagen"
            }
          }
        ]
    """

    # Checking if the happy hour discount is enable
    is_happy_hour = feature_flags.evaluate(name="happy_hour", default=False)

    if is_happy_hour:
        # Enable special discount on happy hour:
        return {"message": "The happy hour discount is enabled."}

    return {"message": "The happy hour discount is not enabled."}
