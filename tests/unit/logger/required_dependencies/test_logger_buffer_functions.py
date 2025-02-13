from aws_lambda_powertools.logging.buffer.functions import _resolve_buffer_log_level


def test_resolve_buffer_log_level_comparison():
    # Test cases where buffer level is lower than current level (should return True)
    assert _resolve_buffer_log_level("DEBUG", "INFO") is True
    assert _resolve_buffer_log_level("DEBUG", "WARNING") is True
    assert _resolve_buffer_log_level("DEBUG", "ERROR") is True
    assert _resolve_buffer_log_level("INFO", "WARNING") is True
    assert _resolve_buffer_log_level("INFO", "ERROR") is True
    assert _resolve_buffer_log_level("WARNING", "ERROR") is True

    # Test cases where buffer level is equal to current level (should return True)
    assert _resolve_buffer_log_level("INFO", "INFO") is True
    assert _resolve_buffer_log_level("DEBUG", "DEBUG") is True
    assert _resolve_buffer_log_level("WARNING", "WARNING") is True
    assert _resolve_buffer_log_level("ERROR", "ERROR") is True
    assert _resolve_buffer_log_level("CRITICAL", "CRITICAL") is True

    # Test cases where buffer level is higher than current level (should return False)
    assert _resolve_buffer_log_level("ERROR", "DEBUG") is False
    assert _resolve_buffer_log_level("CRITICAL", "INFO") is False
    assert _resolve_buffer_log_level("ERROR", "WARNING") is False


def test_resolve_buffer_log_level_case_insensitivity():
    # Test case insensitivity
    assert _resolve_buffer_log_level("debug", "INFO") is True
    assert _resolve_buffer_log_level("DEBUG", "info") is True
    assert _resolve_buffer_log_level("Debug", "Info") is True


def test_resolve_buffer_log_level_edge_cases():
    # Additional edge cases
    assert _resolve_buffer_log_level("DEBUG", "CRITICAL") is True
    assert _resolve_buffer_log_level("CRITICAL", "DEBUG") is False
