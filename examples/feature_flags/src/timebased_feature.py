from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext):
    """
    This feature flag is enabled under the following conditions:
    - The request payload contains a field 'tier' with the value 'premium'.
    - If the current day is either Saturday or Sunday in America/New_York timezone.

    Rule condition to be evaluated:
        "conditions": [
          {
            "action": "EQUALS",
            "key": "tier",
            "value": "premium"
          },
          {
            "action": "SCHEDULE_BETWEEN_DAYS_OF_WEEK",
            "key": "CURRENT_DAY_OF_WEEK",
            "value": {
              "DAYS": [
                "SATURDAY",
                "SUNDAY"
              ],
              "TIMEZONE": "America/New_York"
            }
          }
        ]
    """

    # Get customer's tier from incoming request
    ctx = {"tier": event.get("tier", "standard")}

    # Checking if the weekend premum discount is enable
    weekend_premium_discount = feature_flags.evaluate(name="weekend_premium_discount", default=False, context=ctx)

    if weekend_premium_discount:
        # Enable special discount on weekend for premium users:
        return {"message": "The weekend premium discount is enabled."}

    return {"message": "The weekend premium discount is not enabled."}
