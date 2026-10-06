from __future__ import annotations

from aws_lambda_powertools.utilities.data_classes.common import CaseInsensitiveDict


def test_case_insensitive_dict_init_with_kwargs():
    headers = CaseInsensitiveDict({"Content-Type": "application/json"}, X_Trace_Id="abc")

    assert headers == {"content-type": "application/json", "x_trace_id": "abc"}
    assert headers["x_trace_id"] == "abc"


def test_case_insensitive_dict_update_with_kwargs():
    headers = CaseInsensitiveDict({"Host": "example.com"})
    headers.update(ab="1", User_Agent="test")

    assert headers["AB"] == "1"
    assert headers["user_agent"] == "test"
    assert len(headers) == 3


def test_case_insensitive_dict_copy_keeps_case_insensitive_lookup():
    headers = CaseInsensitiveDict({"Content-Type": "application/json"})
    copied = headers.copy()

    assert isinstance(copied, CaseInsensitiveDict)
    assert copied.get("Content-Type") == "application/json"

    copied["X-Trace-Id"] = "abc"
    assert "x-trace-id" not in headers


def test_case_insensitive_dict_merge_operators():
    headers = CaseInsensitiveDict({"Content-Type": "application/json"})

    merged = headers | {"X-Trace-Id": "abc"}
    assert isinstance(merged, CaseInsensitiveDict)
    assert merged["x-trace-id"] == "abc"
    assert merged["CONTENT-TYPE"] == "application/json"

    merged = {"X-Trace-Id": "abc"} | headers
    assert isinstance(merged, CaseInsensitiveDict)
    assert merged["X-TRACE-ID"] == "abc"

    headers |= {"X-Trace-Id": "abc"}
    assert headers["x-trace-id"] == "abc"
    assert list(headers) == ["content-type", "x-trace-id"]
