from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig
from aws_lambda_powertools.utilities.typing import LambdaContext

logger_buffer_config = LoggerBufferConfig(max_bytes=20480, flush_on_error_log=False)
logger = Logger(level="INFO", buffer_config=logger_buffer_config)


class MyException(Exception):
    pass


@logger.inject_lambda_context(flush_buffer_on_uncaught_error=True)
def lambda_handler(event: dict, context: LambdaContext):
    logger.debug("a debug log")  # this is buffered

    # do stuff

    raise MyException  # Logs will be flushed here
