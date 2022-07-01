from aws_lambda_powertools.metrics import Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext

metrics = Metrics()


@metrics.log_metrics(raise_on_empty_metrics=True)
def lambda_handler(event: dict, context: LambdaContext):
    # no metrics being created will now raise SchemaValidationError
    ...
