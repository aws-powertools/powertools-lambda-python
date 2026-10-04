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
