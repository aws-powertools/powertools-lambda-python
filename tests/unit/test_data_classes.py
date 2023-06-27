import base64
import datetime
import json

import pytest

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    parse_api_gateway_arn,
)
from aws_lambda_powertools.utilities.data_classes.appsync.scalar_types_utils import (
    _formatted_time,
    aws_date,
    aws_datetime,
    aws_time,
    aws_timestamp,
    make_id,
)
from aws_lambda_powertools.utilities.data_classes.common import (
    BaseProxyEvent,
    DictWrapper,
)
from aws_lambda_powertools.utilities.data_classes.event_source import event_source


def test_dict_wrapper_equals():
    class DataClassSample(DictWrapper):
        @property
        def message(self) -> str:
            return self.get("message")

    data1 = {"message": "foo1"}
    data2 = {"message": "foo2"}

    assert DataClassSample(data1) == DataClassSample(data1)
    assert DataClassSample(data1) != DataClassSample(data2)
    # Comparing against a dict should not be equals
    assert DataClassSample(data1) != data1
    assert data1 != DataClassSample(data1)
    assert DataClassSample(data1) is not data1
    assert data1 is not DataClassSample(data1)

    assert DataClassSample(data1).raw_event is data1


def test_dict_wrapper_with_default_custom_json_deserializer():
    class DataClassSample(DictWrapper):
        @property
        def json_body(self) -> dict:
            return self._json_deserializer(self["body"])

    data = {"body": '{"message": "foo1"}'}
    event = DataClassSample(data=data)
    assert event.json_body == json.loads(data["body"])


def test_dict_wrapper_with_valid_custom_json_deserializer():
    class DataClassSample(DictWrapper):
        @property
        def json_body(self) -> dict:
            return self._json_deserializer(self["body"])

    def fake_json_deserializer(record: dict):
        return json.loads(record)

    data = {"body": '{"message": "foo1"}'}
    event = DataClassSample(data=data, json_deserializer=fake_json_deserializer)
    assert event.json_body == json.loads(data["body"])


def test_dict_wrapper_with_invalid_custom_json_deserializer():
    class DataClassSample(DictWrapper):
        @property
        def json_body(self) -> dict:
            return self._json_deserializer(self["body"])

    def fake_json_deserializer() -> None:
        # invalid fn signature should raise TypeError
        pass

    data = {"body": {"message": "foo1"}}
    with pytest.raises(TypeError):
        event = DataClassSample(data=data, json_deserializer=fake_json_deserializer)
        assert event.json_body == {"message": "foo1"}


def test_dict_wrapper_implements_mapping():
    class DataClassSample(DictWrapper):
        pass

    data = {"message": "foo1"}
    event_source = DataClassSample(data)
    assert len(event_source) == len(data)
    assert list(event_source) == list(data)
    assert event_source.keys() == data.keys()
    assert list(event_source.values()) == list(data.values())
    assert event_source.items() == data.items()


def test_dict_wrapper_str_no_property():
    """
    Checks that the _properties function returns
    only the "raw_event", and the resulting string
    notes it as sensitive.
    """

    class DataClassSample(DictWrapper):
        attribute = None

        def function(self) -> None:
            pass

    event_source = DataClassSample({})
    assert str(event_source) == "{'raw_event': '[SENSITIVE]'}"


def test_dict_wrapper_str_single_property():
    """
    Checks that the _properties function returns
    the defined property "data_property", and
    resulting string includes the property value.
    """

    class DataClassSample(DictWrapper):
        attribute = None

        def function(self) -> None:
            pass

        @property
        def data_property(self) -> str:
            return "value"

    event_source = DataClassSample({})
    assert str(event_source) == "{'data_property': 'value', 'raw_event': '[SENSITIVE]'}"


def test_dict_wrapper_str_property_exception():
    """
    Check the recursive _str_helper function handles
    exceptions that may occur when accessing properties
    """

    class DataClassSample(DictWrapper):
        attribute = None

        def function(self) -> None:
            pass

        @property
        def data_property(self):
            raise Exception()

    event_source = DataClassSample({})
    assert str(event_source) == "{'data_property': '[Cannot be deserialized]', 'raw_event': '[SENSITIVE]'}"


def test_dict_wrapper_str_property_list_exception():
    """
    Check that _str_helper properly handles exceptions
    that occur when recursively working through items
    in a list property.
    """

    class BrokenDataClass(DictWrapper):
        @property
        def broken_data_property(self):
            raise Exception()

    class DataClassSample(DictWrapper):
        attribute = None

        def function(self) -> None:
            pass

        @property
        def data_property(self) -> list:
            return ["string", 0, 0.0, BrokenDataClass({})]

    event_source = DataClassSample({})
    event_str = (
        "{'data_property': ['string', 0, 0.0, {'broken_data_property': "
        "'[Cannot be deserialized]', 'raw_event': '[SENSITIVE]'}], 'raw_event': '[SENSITIVE]'}"
    )
    assert str(event_source) == event_str


def test_dict_wrapper_str_recursive_property():
    """
    Check that the _str_helper function recursively
    handles Data Classes within Data Classes
    """

    class DataClassTerminal(DictWrapper):
        attribute = None

        def function(self) -> None:
            pass

        @property
        def terminal_property(self) -> str:
            return "end-recursion"

    class DataClassRecursive(DictWrapper):
        attribute = None

        def function(self) -> None:
            pass

        @property
        def data_property(self) -> DataClassTerminal:
            return DataClassTerminal({})

    event_source = DataClassRecursive({})
    assert (
        str(event_source) == "{'data_property': {'raw_event': '[SENSITIVE]', 'terminal_property': 'end-recursion'},"
        " 'raw_event': '[SENSITIVE]'}"
    )


def test_dict_wrapper_sensitive_properties_property():
    """
    Checks that the _str_helper function correctly
    handles _sensitive_properties
    """

    class DataClassSample(DictWrapper):
        attribute = None

        def function(self) -> None:
            pass

        _sensitive_properties = ["data_property"]

        @property
        def data_property(self) -> str:
            return "value"

    event_source = DataClassSample({})
    assert str(event_source) == "{'data_property': '[SENSITIVE]', 'raw_event': '[SENSITIVE]'}"


def test_base_proxy_event_get_query_string_value():
    default_value = "default"
    set_value = "value"

    event = BaseProxyEvent({})
    value = event.get_query_string_value("test", default_value)
    assert value == default_value

    event._data["queryStringParameters"] = {"test": set_value}
    value = event.get_query_string_value("test", default_value)
    assert value == set_value

    value = event.get_query_string_value("unknown", default_value)
    assert value == default_value

    value = event.get_query_string_value("unknown")
    assert value is None


def test_base_proxy_event_get_header_value():
    default_value = "default"
    set_value = "value"

    event = BaseProxyEvent({"headers": {}})
    value = event.get_header_value("test", default_value)
    assert value == default_value

    event._data["headers"] = {"test": set_value}
    value = event.get_header_value("test", default_value)
    assert value == set_value

    # Verify that the default look is case insensitive
    value = event.get_header_value("Test")
    assert value == set_value

    value = event.get_header_value("unknown", default_value)
    assert value == default_value

    value = event.get_header_value("unknown")
    assert value is None


def test_base_proxy_event_get_header_value_case_insensitive():
    default_value = "default"
    set_value = "value"

    event = BaseProxyEvent({"headers": {}})

    event._data["headers"] = {"Test": set_value}
    value = event.get_header_value("test", case_sensitive=True)
    assert value is None

    value = event.get_header_value("test", default_value=default_value, case_sensitive=True)
    assert value == default_value

    value = event.get_header_value("Test", case_sensitive=True)
    assert value == set_value

    value = event.get_header_value("unknown", default_value, case_sensitive=True)
    assert value == default_value

    value = event.get_header_value("unknown", case_sensitive=True)
    assert value is None


def test_base_proxy_event_json_body_key_error():
    event = BaseProxyEvent({})
    with pytest.raises(KeyError) as ke:
        assert not event.json_body
    assert str(ke.value) == "'body'"


def test_base_proxy_event_json_body():
    data = {"message": "Foo"}
    event = BaseProxyEvent({"body": json.dumps(data)})
    assert event.json_body == data
    assert event.json_body["message"] == "Foo"


def test_base_proxy_event_decode_body_key_error():
    event = BaseProxyEvent({})
    with pytest.raises(KeyError) as ke:
        assert not event.decoded_body
    assert str(ke.value) == "'body'"


def test_base_proxy_event_decode_body_encoded_false():
    data = "Foo"
    event = BaseProxyEvent({"body": data, "isBase64Encoded": False})
    assert event.decoded_body == data


def test_base_proxy_event_decode_body_encoded_true():
    data = "Foo"
    encoded_data = base64.b64encode(data.encode()).decode()
    event = BaseProxyEvent({"body": encoded_data, "isBase64Encoded": True})
    assert event.decoded_body == data


def test_base_proxy_event_json_body_with_base64_encoded_data():
    # GIVEN a base64 encoded json body
    data = {"message": "Foo"}
    data_str = json.dumps(data)
    encoded_data = base64.b64encode(data_str.encode()).decode()
    event = BaseProxyEvent({"body": encoded_data, "isBase64Encoded": True})

    # WHEN calling json_body
    # THEN base64 decode and json load
    assert event.json_body == data


def test_make_id():
    uuid: str = make_id()
    assert isinstance(uuid, str)
    assert len(uuid) == 36


def test_aws_date_utc():
    date_str = aws_date()
    assert isinstance(date_str, str)
    assert datetime.datetime.strptime(date_str, "%Y-%m-%dZ")


def test_aws_time_utc():
    time_str = aws_time()
    assert isinstance(time_str, str)
    assert datetime.datetime.strptime(time_str, "%H:%M:%S.%fZ")


def test_aws_datetime_utc():
    datetime_str = aws_datetime()
    assert datetime.datetime.strptime(datetime_str[:-1] + "000Z", "%Y-%m-%dT%H:%M:%S.%fZ")


def test_format_time_to_milli():
    now = datetime.datetime(2024, 4, 23, 16, 26, 34, 123021)
    datetime_str = _formatted_time(now, "%H:%M:%S.%f", -12)
    assert datetime_str == "04:26:34.123-12:00:00"


def test_aws_timestamp():
    timestamp = aws_timestamp()
    assert isinstance(timestamp, int)


def test_format_time_positive():
    now = datetime.datetime(2022, 1, 22)
    datetime_str = _formatted_time(now, "%Y-%m-%d", 8)
    assert datetime_str == "2022-01-22+08:00:00"


def test_format_time_negative():
    now = datetime.datetime(2022, 1, 22, 14, 22, 33)
    datetime_str = _formatted_time(now, "%H:%M:%S", -12)
    assert datetime_str == "02:22:33-12:00:00"


def test_reflected_types():
    # GIVEN an event_source decorator
    @event_source(data_class=APIGatewayProxyEventV2)
    def lambda_handler(event: APIGatewayProxyEventV2, _):
        # THEN we except the event to be of the pass in data class type
        assert isinstance(event, APIGatewayProxyEventV2)
        assert event.get_header_value("x-foo") == "Foo"

    # WHEN calling the lambda handler
    lambda_handler({"headers": {"X-Foo": "Foo"}}, None)


def test_api_gateway_route_arn_parser():
    """Check api gateway route or method arn parsing"""
    arn = "arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/request"
    details = parse_api_gateway_arn(arn)

    assert details.arn == arn
    assert details.region == "us-east-1"
    assert details.aws_account_id == "123456789012"
    assert details.api_id == "abcdef123"
    assert details.stage == "test"
    assert details.http_method == "GET"
    assert details.resource == "request"

    arn = "arn:aws:execute-api:us-west-2:123456789012:ymy8tbxw7b/*/GET"
    details = parse_api_gateway_arn(arn)
    assert details.resource == ""
    assert details.arn == arn + "/"
