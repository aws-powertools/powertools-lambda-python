"""Unit tests for OpenAPI merge internal functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from aws_lambda_powertools.event_handler.openapi.merge import (
    _discover_resolver_files,
    _file_has_resolver,
    _is_excluded,
    _load_resolver,
)

MERGE_HANDLERS_PATH = Path(__file__).parents[3] / "functional/event_handler/_pydantic/merge_handlers"


# =============================================================================
# _discover_resolver_files
# =============================================================================


def test_discover_resolver_files_path_not_exists():
    with pytest.raises(FileNotFoundError, match="Path does not exist"):
        _discover_resolver_files("/non/existent/path", "**/*.py", [], "app")


def test_discover_resolver_files_multiple_patterns():
    files = _discover_resolver_files(
        MERGE_HANDLERS_PATH,
        ["**/users_handler.py", "**/orders_handler.py"],
        [],
        "app",
    )
    filenames = {f.name for f in files}
    assert "users_handler.py" in filenames
    assert "orders_handler.py" in filenames


# =============================================================================
# _file_has_resolver
# =============================================================================


def test_file_has_resolver_syntax_error(tmp_path: Path):
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken(")
    assert _file_has_resolver(bad_file, "app") is False


def test_file_has_resolver_wrong_variable_name(tmp_path: Path):
    handler_file = tmp_path / "handler.py"
    handler_file.write_text("""
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
router = APIGatewayRestResolver()
""")
    assert _file_has_resolver(handler_file, "app") is False


def test_file_has_resolver_found(tmp_path: Path):
    handler_file = tmp_path / "handler.py"
    handler_file.write_text("""
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
app = APIGatewayRestResolver()
""")
    assert _file_has_resolver(handler_file, "app") is True


# =============================================================================
# _is_excluded
# =============================================================================


def test_is_excluded_with_directory_pattern():
    root = Path("/project")
    assert _is_excluded(Path("/project/tests/handler.py"), root, ["**/tests/**"]) is True
    assert _is_excluded(Path("/project/src/handler.py"), root, ["**/tests/**"]) is False


def test_is_excluded_with_file_pattern():
    root = Path("/project")
    assert _is_excluded(Path("/project/src/test_handler.py"), root, ["**/test_*.py"]) is True
    assert _is_excluded(Path("/project/src/handler.py"), root, ["**/test_*.py"]) is False


# =============================================================================
# _load_resolver
# =============================================================================


def test_load_resolver_file_not_found():
    with pytest.raises(FileNotFoundError):
        _load_resolver(Path("/non/existent/file.py"), "app")


def test_load_resolver_not_found_in_module(tmp_path: Path):
    handler_file = tmp_path / "handler.py"
    handler_file.write_text("x = 1")

    with pytest.raises(AttributeError, match="Resolver 'app' not found"):
        _load_resolver(handler_file, "app")


def test_load_resolver_success(tmp_path: Path):
    handler_file = tmp_path / "handler.py"
    handler_file.write_text("""
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
app = APIGatewayRestResolver()

@app.get("/test")
def test_endpoint():
    return {"test": True}
""")

    resolver = _load_resolver(handler_file, "app")
    assert resolver is not None
    assert hasattr(resolver, "get_openapi_schema")
