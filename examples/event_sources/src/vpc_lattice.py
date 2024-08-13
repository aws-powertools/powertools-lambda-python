from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import VPCLatticeEvent, event_source

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@event_source(data_class=VPCLatticeEvent)
def lambda_handler(event: VPCLatticeEvent, context: LambdaContext):
    logger.info(event.body)

    response = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {"Content-Type": "application/text"},
        "body": "Event Response to VPC Lattice 🔥🚀🔥",
    }

    return response
