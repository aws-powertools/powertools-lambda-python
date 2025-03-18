import json

from aws_lambda_powertools.event_handler import APIGatewayRestResolver


def test_export_openapi_schema_with_custom_configuration():
    # GIVEN an API Gateway resolver with OpenAPI validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # GIVEN custom OpenAPI configuration
    openapi_title = "My API"
    openapi_myapi_version = "1.1.1-alpha"
    app.configure_openapi(title=openapi_title, version=openapi_myapi_version)

    # WHEN we have a simple handler
    @app.get("/")
    def handler():
        pass

    # WHEN we get the schema
    schema = app.get_openapi_schema()

    # THEN the schema should contain our custom configuration
    assert schema.info.title == openapi_title
    assert schema.info.version == openapi_myapi_version


def test_prioritize_direct_parameters_over_stored_configuration():

    # GIVEN
    stored_config = {
        "title": "Stored API Title",
        "version": "1.0.0",
    }

    direct_params = {
        "title": "Direct API Title",
        "version": "2.0.0",
    }

    # GIVEN an API Gateway resolver with OpenAPI validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    app.configure_openapi(**stored_config)

    # WHEN we have a simple handler
    @app.get("/")
    def handler():
        pass

    # WHEN we get the schema with direct params
    schema = app.get_openapi_schema(**direct_params)

    # THEN direct parameters must override stored configuration
    assert schema.info.title == direct_params["title"]
    assert schema.info.version == direct_params["version"]


def test_export_openapi_schema_with_custom_configuration_and_json_export():
    # GIVEN an API Gateway resolver with OpenAPI validation enabled
    app = APIGatewayRestResolver(enable_validation=True)

    # GIVEN custom OpenAPI configuration
    openapi_title = "My API"
    openapi_myapi_version = "1.1.1-alpha"
    openapi_version = "3.1.2"
    openapi_description = "My descrition"
    app.configure_openapi(
        title=openapi_title,
        version=openapi_myapi_version,
        openapi_version=openapi_version,
        description=openapi_description,
    )

    # WHEN we have a simple handler
    @app.get("/")
    def handler():
        pass

    # WHEN we get the schema
    schema = json.loads(app.get_openapi_json_schema())

    # THEN the schema should contain our custom configuration
    assert schema["info"]["title"] == openapi_title
    assert schema["info"]["version"] == openapi_myapi_version
    assert schema["openapi"] == openapi_version
    assert schema["info"]["description"] == openapi_description
