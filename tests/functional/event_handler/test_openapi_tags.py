from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.models import Tag


def test_openapi_with_tags():
    app = APIGatewayRestResolver()

    @app.get("/users")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema(tags=["Orders"])
    assert schema.tags is not None
    assert len(schema.tags) == 1

    tag = schema.tags[0]
    assert tag.name == "Orders"


def test_openapi_with_object_tags():
    app = APIGatewayRestResolver()

    @app.get("/users")
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema(tags=[Tag(name="Orders", description="Order description tag")])
    assert schema.tags is not None
    assert len(schema.tags) == 1

    tag = schema.tags[0]
    assert tag.name == "Orders"
    assert tag.description == "Order description tag"


def test_openapi_operation_with_tags():
    app = APIGatewayRestResolver()

    @app.get("/users", tags=["Users"])
    def handler():
        raise NotImplementedError()

    schema = app.get_openapi_schema()
    assert schema.paths is not None
    assert len(schema.paths.keys()) == 1

    get = schema.paths["/users"].get
    assert get is not None
    assert get.tags is not None
    assert len(get.tags) == 1

    tag = get.tags[0]
    assert tag == "Users"
