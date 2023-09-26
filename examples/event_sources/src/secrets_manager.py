from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.data_classes import SecretsManagerEvent, event_source

secrets_provider = parameters.SecretsProvider()


@event_source(data_class=SecretsManagerEvent)
def lambda_handler(event: SecretsManagerEvent, context):
    # Getting secret value using Parameter utility
    # See https://docs.powertools.aws.dev/lambda/python/latest/utilities/parameters/
    secret = secrets_provider.get(event.secret_id, VersionId=event.version_id, VersionStage="AWSCURRENT")

    # You need to work with secrets afterwards
    # Check more examples: https://github.com/aws-samples/aws-secrets-manager-rotation-lambdas

    return secret
