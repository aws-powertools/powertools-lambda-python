from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import VPCLatticeEventV2, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@event_source(data_class=VPCLatticeEventV2)
def lambda_handler(event: VPCLatticeEventV2, context: LambdaContext):
    logger.info(event.body)

    response = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "statusDescription": "200 OK",
        "headers": {"Content-Type": "application/text"},
        "body": "VPC Lattice V2 Event ✨🎉✨",
    }

    return response
