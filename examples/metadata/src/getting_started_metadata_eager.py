from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.metadata import LambdaMetadata, get_lambda_metadata
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# Fetch during cold start — cached for subsequent invocations
metadata: LambdaMetadata = get_lambda_metadata()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.append_keys(az_id=metadata.availability_zone_id)
    logger.info("Processing request")

    return {"az_id": metadata.availability_zone_id}
