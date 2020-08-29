# -*- coding: utf-8 -*-
from aws_lambda_powertools.utilities.typing import LambdaClientContext, LambdaCognitoIdentity


class LambdaContext(object):
    """The LambdaContext static object can be used to ease the development by providing the IDE type hints.

    Example
    -------
    **A Lambda function using LambdaContext**

        >>> from aws_lambda_powertools.utilities.typing import LambdaDict, LambdaContext
        >>>
        >>> def handler(event: LambdaDict, context: LambdaContext) -> LambdaDict:
        >>>     # Insert business logic
        >>>     return event

    """

    function_name: str
    function_version: str
    invoked_function_arn: str
    memory_limit_in_mb: int
    aws_request_id: str
    log_group_name: str
    log_stream_name: str
    identity: LambdaCognitoIdentity
    client_context: LambdaClientContext

    @staticmethod
    def get_remaining_time_in_millis() -> int:
        """

        Returns
        -------

        """
        return 0
