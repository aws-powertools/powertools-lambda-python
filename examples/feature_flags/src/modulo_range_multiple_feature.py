from aws_lambda_powertools.utilities.feature_flags import AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.typing import LambdaContext

app_config = AppConfigStore(environment="dev", application="product-catalogue", name="features")

feature_flags = FeatureFlags(store=app_config)


def lambda_handler(event: dict, context: LambdaContext):
    """
    This non-boolean feature flag returns the percentage discount depending on the sale experiment segment:
    - 10% standard discount if the user_id belongs to the spectrum 0-3 modulo 10, (40% users).
    - 15% experiment discount if the user_id belongs to the spectrum 4-6 modulo 10, (30% users).
    - 18% experiment discount if the user_id belongs to the spectrum 7-9 modulo 10, (30% users).

    Rule conditions to be evaluated:
    "rules": {
      "control group - standard 10% discount segment": {
        "when_match": 10,
        "conditions": [
          {
            "action": "MODULO_RANGE",
            "key": "user_id",
            "value": {
              "BASE": 10,
              "START": 0,
              "END": 3
            }
          }
        ]
      },
      "test experiment 1 - 15% discount segment": {
        "when_match": 15,
        "conditions": [
          {
            "action": "MODULO_RANGE",
            "key": "user_id",
            "value": {
              "BASE": 10,
              "START": 4,
              "END": 6
            }
          }
        ]
      },
      "test experiment 2 - 18% discount segment": {
        "when_match": 18,
        "conditions": [
          {
            "action": "MODULO_RANGE",
            "key": "user_id",
            "value": {
              "BASE": 10,
              "START": 7,
              "END": 9
            }
          }
        ]
      }
    }
    """

    # Get customer's tier and identifier from incoming request
    ctx = {"tier": event.get("tier", "standard"), "user_id": event.get("user_id", 0)}

    # Get sale discount percentage from feature flag.
    sale_experiment_discount = feature_flags.evaluate(name="sale_experiment_discount", default=0, context=ctx)

    return {"message": f" {sale_experiment_discount}% discount applied."}
