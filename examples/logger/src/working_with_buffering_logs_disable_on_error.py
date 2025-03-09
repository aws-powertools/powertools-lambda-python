from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig
from aws_lambda_powertools.utilities.typing import LambdaContext

logger_buffer_config = LoggerBufferConfig(flush_on_error_log=False)  # (1)!
logger = Logger(level="INFO", buffer_config=logger_buffer_config)


class MyException(Exception):
    pass


def lambda_handler(event: dict, context: LambdaContext):
    logger.debug("a debug log")  # this is buffered

    # do stuff

    try:
        raise MyException
    except MyException as error:
        logger.error("An error ocurrend", exc_info=error)  # Logs won't be flushed here

    # Need to flush logs manually
    logger.flush_buffer()
