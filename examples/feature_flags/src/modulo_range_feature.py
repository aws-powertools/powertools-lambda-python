from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext):
    """
    This feature flag is enabled under the following conditions:
    - The request payload contains a field 'tier' with the value 'standard'.
    - If the user_id belongs to the spectrum 0-19 modulo 100, (20% users) on whom we want to run the sale experiment.

    Rule condition to be evaluated:
        "conditions": [
          {
            "action": "EQUALS",
            "key": "tier",
            "value": "standard"
          },
          {
            "action": "MODULO_RANGE",
            "key": "user_id",
            "value": {
              "BASE": 100,
              "START": 0,
              "END": 19
            }
          }
        ]
    """

    # Get customer's tier and identifier from incoming request
    ctx = {"tier": event.get("tier", "standard"), "user_id": event.get("user_id", 0)}

    # Checking if the sale_experiment is enable
    sale_experiment = feature_flags.evaluate(name="sale_experiment", default=False, context=ctx)

    if sale_experiment:
        # Enable special discount for sale experiment segment users:
        return {"message": "The sale experiment is enabled."}

    return {"message": "The sale experiment is not enabled."}
