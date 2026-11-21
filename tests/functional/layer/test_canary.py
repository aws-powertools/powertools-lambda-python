import importlib.util
import sys
from importlib.metadata import version
from pathlib import Path

import pytest


@pytest.fixture
def canary(monkeypatch, mocker):
    root = Path(__file__).parents[3] / "layer_v3" / "layer" / "canary"
    monkeypatch.syspath_prepend(str(root))
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "true")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    # Tracer initialization changes global X-Ray state; exercise it in the deployed canary.
    mocker.patch("aws_lambda_powertools.Tracer")
    spec = importlib.util.spec_from_file_location("layer_canary_test", root / "app.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "layer_arn", "arn:aws:lambda:us-east-1:123456789012:layer:test:1")
    monkeypatch.setattr(module, "powertools_version", version("aws_lambda_powertools"))
    monkeypatch.setattr(module, "stage", "BETA")
    monkeypatch.setattr(module, "event_bus_arn", "arn:aws:events:us-east-1:123456789012:event-bus/test")
    monkeypatch.setattr(module, "import_compilations", [])
    return module


def test_canary_validates_before_notifying(canary, mocker):
    notify = mocker.patch.object(canary, "send_notification")
    assert canary.handler({}) is True
    notify.assert_called_once_with()


def test_canary_rejects_recompiled_layer_before_notifying(canary, monkeypatch, mocker):
    monkeypatch.setattr(canary, "import_compilations", ["/opt/python/package/model.py"])
    notify = mocker.patch.object(canary, "send_notification")

    with pytest.raises(ValueError, match="Layer recompiled"):
        canary.handler({})

    notify.assert_not_called()


def test_canary_rejects_compilation_during_checks(canary, mocker):
    from importlib.machinery import SourceFileLoader

    def compile_layer_source():
        source = "/opt/python/package/late_import.py"
        SourceFileLoader("late_import", source).source_to_code(b"value = 42", source)

    mocker.patch.object(canary, "verify_layer_functionality", side_effect=compile_layer_source)
    notify = mocker.patch.object(canary, "send_notification")

    with pytest.raises(ValueError, match="late_import.py"):
        canary.handler({})

    notify.assert_not_called()


@pytest.mark.parametrize("request_type", ["Delete", "Update"])
def test_canary_can_be_deleted_after_cache_failure(canary, monkeypatch, mocker, request_type):
    monkeypatch.setattr(canary, "import_compilations", ["/opt/python/package/model.py"])
    check = mocker.patch.object(canary, "handler", side_effect=ValueError("cache failure"))

    assert canary.on_event.__wrapped__({"RequestType": request_type}, None) == "Nothing to be processed"
    check.assert_not_called()


def test_canary_create_runs_checks(canary, mocker):
    check = mocker.patch.object(canary, "handler")
    event = {"RequestType": "Create", "ResourceProperties": {}}

    canary.on_event.__wrapped__(event, None)

    check.assert_called_once_with(event)


def test_canary_rejects_missing_source_before_notifying(canary, mocker):
    mocker.patch.object(canary.inspect, "getsource", side_effect=OSError("source missing"))
    notify = mocker.patch.object(canary, "send_notification")

    with pytest.raises(OSError, match="source missing"):
        canary.handler({})

    notify.assert_not_called()


def test_canary_rejects_version_mismatch_before_notifying(canary, monkeypatch, mocker):
    monkeypatch.setattr(canary, "powertools_version", "0.0.0")
    notify = mocker.patch.object(canary, "send_notification")

    with pytest.raises(ValueError, match="Expected Powertools version"):
        canary.handler({})

    notify.assert_not_called()
