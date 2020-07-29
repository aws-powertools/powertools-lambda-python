"""
Parameter retrieval and caching utility
"""


from collections import namedtuple
from datetime import datetime, timedelta

import boto3

DEFAULT_MAX_AGE = 5
ExpirableValue = namedtuple("ExpirableValue", ["value", "ttl"])
PARAMETER_VALUES = {}
ssm = boto3.client("ssm")


def get_parameter(name: str, max_age: int = DEFAULT_MAX_AGE) -> str:
    """
    Retrieve a parameter from the AWS Systems Manager (SSM) Parameter Store

    This will keep a local version in cache for `max_age` seconds to prevent
    overfetching from SSM Parameter Store.

    See the [AWS Systems Manager Parameter Store documentation]
    (https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
    for more information.

    Parameters
    ----------
    name: str
        Name of the SSM Parameter
    max_age: int
        Duration for which the parameter value can be cached

    Example
    -------

        from aws_lambda_powertools.utilities import get_parameter

        def lambda_handler(event, context):
            # This will only make a call to the SSM service every 30 seconds.
            value = get_parameter("my-parameter", max_age=30)

    Raises
    ------
    ssm.exceptions.InternalServerError
        When there is an internal server error from AWS Systems Manager
    ssm.exceptions.InvalidKeyId
        When the key ID is invalid
    ssm.exceptions.ParameterNotFound
        When the parameter name is not found in AWS Systems Manager
    ssm.exceptions.ParameterVersionNotFound
        When a version of the parameter is not found in AWS Systems Manager
    """

    if name not in PARAMETER_VALUES or PARAMETER_VALUES[name].ttl < datetime.now():
        # Retrieve the parameter from AWS Systems Manager
        parameter = ssm.get_parameter(Name=name)
        PARAMETER_VALUES[name] = ExpirableValue(
            parameter["Parameter"]["Value"], datetime.now() + timedelta(seconds=max_age)
        )

    return PARAMETER_VALUES[name].value
