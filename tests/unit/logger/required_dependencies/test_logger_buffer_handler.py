from __future__ import annotations

import io
import json
import logging

from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging.buffer.config import LoggerBufferConfig
from aws_lambda_powertools.logging.buffer.handler import BufferingHandler
from aws_lambda_powertools.shared import constants


def test_buffering_handler_init_stores_dependencies():
    # GIVEN real buffer_config, source_logger (Logger with buffer), and its buffer_cache
    buffer_config = LoggerBufferConfig(max_bytes=10240)
    source_logger = Logger(service="test1", buffer_config=buffer_config, stream=io.StringIO())
    buffer_cache = source_logger._buffer_cache

    # WHEN BufferingHandler is initialized
    handler = BufferingHandler(
        buffer_cache=buffer_cache,
        buffer_config=buffer_config,
        source_logger=source_logger,
    )

    # THEN all dependencies are stored on the instance
    assert handler.buffer_cache is buffer_cache
    assert handler.buffer_config is buffer_config
    assert handler.source_logger is source_logger
    assert handler.level == logging.NOTSET


def test_buffering_handler_emit_calls_add_log_record_to_buffer(monkeypatch):
    # GIVEN a real Logger with buffer and a BufferingHandler (tracer id set so records are buffered)
    # Using buffer_at_verbosity="WARNING" so INFO logs are buffered (below threshold)
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")
    stream = io.StringIO()
    buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="WARNING")
    source_logger = Logger(service="test2", buffer_config=buffer_config, stream=stream)
    handler = BufferingHandler(
        buffer_cache=source_logger._buffer_cache,
        buffer_config=source_logger._buffer_config,
        source_logger=source_logger,
    )
    record = logging.LogRecord(
        name="external",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test %s",
        args=("arg",),
        exc_info=None,
        func=None,
    )
    record.stack_info = None

    # WHEN the handler emits the record and the buffer is flushed
    handler.emit(record)

    # THEN the message is NOT in output yet (it's buffered)
    assert "test arg" not in stream.getvalue()

    # AND when buffer is flushed, the buffered message appears in the logger output
    source_logger.flush_buffer()
    output = stream.getvalue()
    log_line = json.loads(output.strip())
    assert log_line["message"] == "test arg"


def test_buffering_handler_emit_above_threshold_emits_directly(monkeypatch):
    # GIVEN a real Logger with buffer_at_verbosity="DEBUG" (default)
    # INFO logs should be emitted directly since INFO > DEBUG
    monkeypatch.setenv(constants.XRAY_TRACE_ID_ENV, "1-67c39786-5908a82a246fb67f3089263f")
    stream = io.StringIO()
    buffer_config = LoggerBufferConfig(max_bytes=10240, buffer_at_verbosity="DEBUG")
    source_logger = Logger(service="test3", buffer_config=buffer_config, stream=stream)
    handler = BufferingHandler(
        buffer_cache=source_logger._buffer_cache,
        buffer_config=source_logger._buffer_config,
        source_logger=source_logger,
    )
    record = logging.LogRecord(
        name="external",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="direct message",
        args=(),
        exc_info=None,
        func=None,
    )
    record.stack_info = None

    # WHEN the handler emits the record
    handler.emit(record)

    # THEN the message appears immediately (not buffered)
    output = stream.getvalue()
    assert "direct message" in output
