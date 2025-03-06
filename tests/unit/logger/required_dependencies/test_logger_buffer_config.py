import pytest

from aws_lambda_powertools.logging.buffer import LoggerBufferConfig


def test_default_configuration():
    # GIVEN no specific configuration parameters
    config_buffer = LoggerBufferConfig()

    # THEN default values are default
    assert config_buffer.max_bytes == 20480
    assert config_buffer.buffer_at_verbosity == "DEBUG"
    assert config_buffer.flush_on_error_log is True


def test_custom_configuration():
    # GIVEN a new LoggerBufferConfig with custom configuration parameters
    config_buffer = LoggerBufferConfig(
        max_bytes=51200,
        buffer_at_verbosity="WARNING",
        flush_on_error_log=False,
    )

    # THEN configuration is set with provided values
    assert config_buffer.max_bytes == 51200
    assert config_buffer.buffer_at_verbosity == "WARNING"
    assert config_buffer.flush_on_error_log is False


def test_invalid_max_size_negative():
    # GIVEN an invalid negative max size
    invalid_max_size = -100

    # WHEN creating a LoggerBufferConfig
    with pytest.raises(ValueError, match="Max size must be a positive integer"):
        # THEN a ValueError is raised
        LoggerBufferConfig(max_bytes=invalid_max_size)


def test_invalid_max_size_type():
    # GIVEN an invalid max size type
    invalid_max_size = "10240"

    # WHEN creating a LoggerBufferConfig
    with pytest.raises(ValueError, match="Max size must be a positive integer"):
        # THEN a ValueError is raised
        LoggerBufferConfig(max_bytes=invalid_max_size)


def test_invalid_log_level():
    # GIVEN an invalid log level
    invalid_log_levels = ["INVALID_LEVEL", 123, None]

    # WHEN creating a LoggerBufferConfig
    for invalid_log_level in invalid_log_levels:
        # THEN a ValueError is raised
        with pytest.raises(ValueError):
            LoggerBufferConfig(buffer_at_verbosity=invalid_log_level)


def test_case_insensitive_log_level():
    # GIVEN
    test_cases = ["debug", "Info", "WARNING"]

    # WHEN / THEN
    for log_level in test_cases:
        config = LoggerBufferConfig(buffer_at_verbosity=log_level)
        assert config.buffer_at_verbosity == log_level.upper()


def test_invalid_flush_on_error():
    # GIVEN an invalid flush_on_error type
    invalid_flush_on_error = "True"

    # WHEN creating a LoggerBufferConfig / THEN
    with pytest.raises(ValueError, match="flush_on_error must be a boolean"):
        # THEN a ValueError is raised
        LoggerBufferConfig(flush_on_error_log=invalid_flush_on_error)
