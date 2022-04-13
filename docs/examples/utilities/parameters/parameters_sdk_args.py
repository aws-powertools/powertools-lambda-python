from aws_lambda_powertools.utilities import parameters

secrets_provider = parameters.SecretsProvider()


def handler(event, context):
    # The 'VersionId' argument will be passed to the underlying get_secret_value() call.
    value = secrets_provider.get("my-secret", VersionId="e62ec170-6b01-48c7-94f3-d7497851a8d2")
