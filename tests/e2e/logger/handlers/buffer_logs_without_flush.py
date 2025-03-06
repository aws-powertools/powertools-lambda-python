from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig

logger_buffer_config = LoggerBufferConfig(max_bytes=10240)

logger = Logger(level="INFO", buffer_config=logger_buffer_config)


def lambda_handler(event, context):
    message_visible, message_buffered = event.get("message_visible", ""), event.get("message_buffered", {})
    logger.info(message_visible)
    logger.debug(message_buffered)
    return "success"
