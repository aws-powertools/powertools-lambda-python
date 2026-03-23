from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.metadata import LambdaMetadata, get_lambda_metadata
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    metadata: LambdaMetadata = get_lambda_metadata()
    az_id = metadata.availability_zone_id  # e.g., "use1-az1"

    logger.append_keys(az_id=az_id)
    logger.info("Processing request")

    return {"az_id": az_id}
