from working_with_buffering_logs_creating_instance import logger  # reusing same instance
from working_with_buffering_logs_reusing_function import my_function

from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext):
    logger.debug("a debug log")  # this is buffered

    my_function()

    logger.flush_buffer()
