import asyncio
import datetime
import json
import os
import sys

import pytest

from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEvent
from aws_lambda_powertools.utilities.data_classes.appsync.resolver_utils import AppSyncResolver
from aws_lambda_powertools.utilities.data_classes.appsync.scalar_types_utils import (
    _formatted_time,
    aws_date,
    aws_datetime,
    aws_time,
    aws_timestamp,
    make_id,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


def load_event(file_name: str) -> dict:
    full_file_name = os.path.dirname(os.path.realpath(__file__)) + "/../../events/" + file_name
    with open(full_file_name) as fp:
        return json.load(fp)


def test_direct_resolver():
    # Check whether we can handle an example appsync direct resolver
    mock_event = load_event("appSyncDirectResolver.json")

    app = AppSyncResolver()

    @app.resolver(field_name="createSomething", include_context=True)
    def create_something(context, id: str):  # noqa AA03 VNE003
        assert context == {}
        return id

    def handler(event, context):
        return app.resolve(event, context)

    result = handler(mock_event, {})
    assert result == "my identifier"


def test_amplify_resolver():
    # Check whether we can handle an example appsync resolver
    mock_event = load_event("appSyncResolverEvent.json")

    app = AppSyncResolver()

    @app.resolver(type_name="Merchant", field_name="locations", include_event=True)
    def get_location(event: AppSyncResolverEvent, page: int, size: int, name: str):
        assert event is not None
        assert page == 2
        assert size == 1
        return name

    def handler(event, context):
        return app.resolve(event, context)

    result = handler(mock_event, {})
    assert result == "value"


def test_resolver_no_params():
    # GIVEN
    app = AppSyncResolver()

    @app.resolver(type_name="Query", field_name="noParams")
    def no_params():
        return "no_params has no params"

    event = {"typeName": "Query", "fieldName": "noParams", "arguments": {}}

    # WHEN
    result = app.resolve(event, LambdaContext())

    # THEN
    assert result == "no_params has no params"


def test_resolver_include_event():
    # GIVEN
    app = AppSyncResolver()

    mock_event = {"typeName": "Query", "fieldName": "field", "arguments": {}}

    @app.resolver(field_name="field", include_event=True)
    def get_value(event: AppSyncResolverEvent):
        return event

    # WHEN
    result = app.resolve(mock_event, LambdaContext())

    # THEN
    assert result._data == mock_event
    assert isinstance(result, AppSyncResolverEvent)


def test_resolver_include_context():
    # GIVEN
    app = AppSyncResolver()

    mock_event = {"typeName": "Query", "fieldName": "field", "arguments": {}}

    @app.resolver(field_name="field", include_context=True)
    def get_value(context: LambdaContext):
        return context

    # WHEN
    mock_context = LambdaContext()
    result = app.resolve(mock_event, mock_context)

    # THEN
    assert result == mock_context


def test_resolver_value_error():
    # GIVEN no defined field resolver
    app = AppSyncResolver()

    # WHEN
    with pytest.raises(ValueError) as exp:
        event = {"typeName": "type", "fieldName": "field", "arguments": {}}
        app.resolve(event, LambdaContext())

    # THEN
    assert exp.value.args[0] == "No resolver found for 'type.field'"


def test_resolver_yield():
    # GIVEN
    app = AppSyncResolver()

    mock_event = {"typeName": "Customer", "fieldName": "field", "arguments": {}}

    @app.resolver(field_name="field")
    def func_yield():
        yield "value"

    # WHEN
    mock_context = LambdaContext()
    result = app.resolve(mock_event, mock_context)

    # THEN
    assert next(result) == "value"


def test_resolver_multiple_mappings():
    # GIVEN
    app = AppSyncResolver()

    @app.resolver(field_name="listLocations")
    @app.resolver(field_name="locations")
    def get_locations(name: str, description: str = ""):
        return name + description

    # WHEN
    mock_event1 = {"typeName": "Query", "fieldName": "listLocations", "arguments": {"name": "value"}}
    mock_event2 = {
        "typeName": "Merchant",
        "fieldName": "locations",
        "arguments": {"name": "value2", "description": "description"},
    }
    result1 = app.resolve(mock_event1, LambdaContext())
    result2 = app.resolve(mock_event2, LambdaContext())

    # THEN
    assert result1 == "value"
    assert result2 == "value2description"


@pytest.mark.skipif(sys.version_info < (3, 8), reason="only for python versions that support asyncio.run")
def test_resolver_async():
    # GIVEN
    app = AppSyncResolver()

    mock_event = {"typeName": "Customer", "fieldName": "field", "arguments": {}}

    @app.resolver(field_name="field")
    async def get_async():
        await asyncio.sleep(0.0001)
        return "value"

    # WHEN
    mock_context = LambdaContext()
    result = app.resolve(mock_event, mock_context)

    # THEN
    assert asyncio.run(result) == "value"


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
    assert datetime.datetime.strptime(time_str, "%H:%M:%SZ")


def test_aws_datetime_utc():
    datetime_str = aws_datetime()
    assert isinstance(datetime_str, str)
    assert datetime.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")


def test_aws_timestamp():
    timestamp = aws_timestamp()
    assert isinstance(timestamp, int)


def test_format_time_positive():
    now = datetime.datetime(2022, 1, 22)
    datetime_str = _formatted_time(now, "%Y-%m-%d", 8)
    assert isinstance(datetime_str, str)
    assert datetime_str == "2022-01-22+08:00:00"


def test_format_time_negative():
    now = datetime.datetime(2022, 1, 22, 14, 22, 33)
    datetime_str = _formatted_time(now, "%H:%M:%S", -12)
    assert isinstance(datetime_str, str)
    assert datetime_str == "02:22:33-12:00:00"
