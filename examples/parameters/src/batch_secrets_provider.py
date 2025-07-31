from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.parameters import SecretsProvider
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
# Create provider instance for more control
secrets_provider = SecretsProvider()


def lambda_handler(event, context: LambdaContext):
    # Retrieve secrets with custom settings
    secrets = secrets_provider.get_multiple(
        names=["service/auth-token", "service/encryption-key"],
        max_age=600,  # Cache for 10 minutes
        transform="json",  # Parse JSON secrets
        raise_on_transform_error=False,  # Don't fail on transform errors
    )

    # Handle potential transform failures
    auth_token = secrets.get("service/auth-token")
    encryption_key = secrets.get("service/encryption-key")

    if auth_token is None:
        logger.info("Warning: auth-token failed to parse as JSON")
    if encryption_key is None:
        logger.info("Warning: encryption-key failed to parse as JSON")

    return {
        "statusCode": 200,
        "body": f"Retrieved {len([s for s in secrets.values() if s is not None])} valid secrets",
    }
