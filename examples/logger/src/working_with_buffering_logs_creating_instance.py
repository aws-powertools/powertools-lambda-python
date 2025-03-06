from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig

logger_buffer_config = LoggerBufferConfig(max_bytes=20480, buffer_at_verbosity="WARNING")
logger = Logger(level="INFO", buffer_config=logger_buffer_config)
