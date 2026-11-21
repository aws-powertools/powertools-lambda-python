from typing import Any

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

# Reads from the AWS AppConfig Agent Lambda extension on localhost; no boto3 call is made
appconfig = parameters.AppConfigExtensionProvider(environment="dev", application="comments")


def lambda_handler(event: dict, context: LambdaContext) -> dict[str, Any]:
    # The extension caches and refreshes the configuration in the background
    config: Any = appconfig.get("config", transform="json", max_age=0)

    return {"statusCode": 200, "body": config}
