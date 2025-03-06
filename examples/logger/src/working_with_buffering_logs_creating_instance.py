from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer import LoggerBufferConfig

logger_buffer_config = LoggerBufferConfig(max_size=20480, minimum_log_level="WARNING")
logger = Logger(level="INFO", logger_buffer=logger_buffer_config)
