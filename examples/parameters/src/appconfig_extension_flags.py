from typing import Any

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

appconfig = parameters.AppConfigExtensionProvider(environment="dev", application="comments")


def lambda_handler(event: dict, context: LambdaContext) -> dict[str, Any]:
    # Any keyword argument becomes a query string parameter sent to the extension
    flags: Any = appconfig.get("features", transform="json", flag=["new_editor", "dark_mode"])

    return {"statusCode": 200, "body": flags}
