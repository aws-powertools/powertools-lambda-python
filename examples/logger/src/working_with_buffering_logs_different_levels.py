from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig
from aws_lambda_powertools.utilities.typing import LambdaContext

logger_buffer_config = LoggerBufferConfig(buffer_at_verbosity="WARNING")  # (1)!
logger = Logger(level="INFO", buffer_config=logger_buffer_config)


def lambda_handler(event: dict, context: LambdaContext):
    logger.warning("a warning log")  # this is buffered
    logger.info("an info log")  # this is buffered
    logger.debug("a debug log")  # this is buffered

    # do stuff

    logger.flush_buffer()
