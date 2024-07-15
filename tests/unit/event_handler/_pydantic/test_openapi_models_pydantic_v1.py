import pytest

from aws_lambda_powertools.event_handler.openapi.exceptions import SchemaValidationError
from aws_lambda_powertools.event_handler.openapi.models import OpenAPIExtensions


@pytest.mark.usefixtures("pydanticv1_only")
def test_openapi_extensions_with_dict():
    # GIVEN we create an OpenAPIExtensions object with a dict
    extensions = OpenAPIExtensions(openapi_extensions={"x-amazon-apigateway": {"foo": "bar"}})

    # THEN we get a dict with the extension
    assert extensions.dict(exclude_none=True) == {"x-amazon-apigateway": {"foo": "bar"}}


@pytest.mark.usefixtures("pydanticv1_only")
def test_openapi_extensions_with_invalid_key():
    # GIVEN we create an OpenAPIExtensions object with an invalid value
    with pytest.raises(SchemaValidationError):
        # THEN must raise an exception
        OpenAPIExtensions(openapi_extensions={"amazon-apigateway-invalid": {"foo": "bar"}})


@pytest.mark.usefixtures("pydanticv1_only")
def test_openapi_extensions_with_proxy_models():

    # GIVEN we create an models using OpenAPIExtensions as a "Proxy" Model
    class MyModelFoo(OpenAPIExtensions):
        foo: str

    class MyModelBar(OpenAPIExtensions):
        bar: str
        foo: MyModelFoo

    value_to_serialize = MyModelBar(
        bar="bar",
        foo=MyModelFoo(foo="foo"),
        openapi_extensions={"x-amazon-apigateway": {"foo": "bar"}},
    )

    value_to_return = value_to_serialize.dict(exclude_none=True)

    # THEN we get a dict with the value serialized
    assert value_to_return == {"bar": "bar", "foo": {"foo": "foo"}, "x-amazon-apigateway": {"foo": "bar"}}
