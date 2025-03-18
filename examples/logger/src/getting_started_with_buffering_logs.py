from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig
from aws_lambda_powertools.utilities.typing import LambdaContext

logger_buffer_config = LoggerBufferConfig(max_bytes=20480, flush_on_error_log=True)
logger = Logger(level="INFO", buffer_config=logger_buffer_config)


def lambda_handler(event: dict, context: LambdaContext):
    logger.debug("a debug log")  # this is buffered
    logger.info("an info log")  # this is not buffered

    # do stuff

    logger.flush_buffer()
