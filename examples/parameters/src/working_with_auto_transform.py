from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities import parameters

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext

ssm_provider = parameters.SSMProvider()


def lambda_handler(event: dict, context: LambdaContext):
    values = ssm_provider.get_multiple("/param", transform="auto")

    return values
