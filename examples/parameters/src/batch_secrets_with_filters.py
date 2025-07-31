from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def lambda_handler(event, context: LambdaContext):
    # Retrieve secrets with additional filtering
    production_secrets = parameters.get_secrets_by_name(
        names=["app-secret", "db-secret"],
        Filters=[
            {"Key": "primary-region", "Values": ["us-east-1"]},
            {"Key": "tag-value", "Values": ["production"]},
        ],
    )

    # Only secrets matching ALL filters will be returned
    for name, _ in production_secrets.items():
        logger.info(f"Found production secret: {name}")

    return {
        "statusCode": 200,
        "body": f"Retrieved {len(production_secrets)} production secrets",
    }
