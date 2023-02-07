from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

secrets_provider = parameters.SecretsProvider()


def lambda_handler(event: dict, context: LambdaContext):
    # The 'VersionId' argument will be passed to the underlying get_secret_value() call.
    value = secrets_provider.get("my-secret", VersionId="e62ec170-6b01-48c7-94f3-d7497851a8d2")

    return value
