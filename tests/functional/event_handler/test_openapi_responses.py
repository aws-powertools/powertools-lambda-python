from aws_lambda_powertools.event_handler import APIGatewayRestResolver


def test_openapi_default_response():
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/")
    def handler():
        pass

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 200 in responses.keys()
    assert responses[200].description == "Successful Response"

    assert 422 in responses.keys()
    assert responses[422].description == "Validation Error"


def test_openapi_200_response_with_description():
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/", response_description="Custom response")
    def handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 200 in responses.keys()
    assert responses[200].description == "Custom response"

    assert 422 in responses.keys()
    assert responses[422].description == "Validation Error"


def test_openapi_200_custom_response():
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/", responses={202: {"description": "Custom response"}})
    def handler():
        return {"message": "hello world"}

    schema = app.get_openapi_schema()
    responses = schema.paths["/"].get.responses
    assert 202 in responses.keys()
    assert responses[202].description == "Custom response"

    assert 200 not in responses.keys()
    assert 422 not in responses.keys()
