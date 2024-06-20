from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    LambdaFunctionUrlResolver,
    VPCLatticeResolver,
    VPCLatticeV2Resolver,
)
from tests.functional.utils import load_event


def test_base_path_api_gateway_rest():
    app = APIGatewayRestResolver()

    @app.get("/")
    def handle():
        return app._get_base_path()

    event = load_event("apiGatewayProxyEvent.json")
    event["path"] = "/"

    result = app(event, {})
    assert result["statusCode"] == 200
    assert result["body"] == ""


def test_base_path_api_gateway_http():
    app = APIGatewayHttpResolver()

    @app.get("/")
    def handle():
        return app._get_base_path()

    event = load_event("apiGatewayProxyV2Event.json")
    event["rawPath"] = "/"
    event["requestContext"]["http"]["path"] = "/"
    event["requestContext"]["http"]["method"] = "GET"

    result = app(event, {})
    assert result["statusCode"] == 200
    assert result["body"] == ""


def test_base_path_alb():
    app = ALBResolver()

    @app.get("/")
    def handle():
        return app._get_base_path()

    event = load_event("albEvent.json")
    event["path"] = "/"

    result = app(event, {})
    assert result["statusCode"] == 200
    assert result["body"] == ""


def test_base_path_lambda_function_url():
    app = LambdaFunctionUrlResolver()

    @app.get("/")
    def handle():
        return app._get_base_path()

    event = load_event("lambdaFunctionUrlIAMEvent.json")
    event["rawPath"] = "/"
    event["requestContext"]["http"]["path"] = "/"
    event["requestContext"]["http"]["method"] = "GET"

    result = app(event, {})
    assert result["statusCode"] == 200
    assert result["body"] == ""


def test_vpc_lattice():
    app = VPCLatticeResolver()

    @app.get("/")
    def handle():
        return app._get_base_path()

    event = load_event("vpcLatticeEvent.json")
    event["raw_path"] = "/"

    result = app(event, {})
    assert result["statusCode"] == 200
    assert result["body"] == ""


def test_vpc_latticev2():
    app = VPCLatticeV2Resolver()

    @app.get("/")
    def handle():
        return app._get_base_path()

    event = load_event("vpcLatticeV2Event.json")
    event["path"] = "/"

    result = app(event, {})
    assert result["statusCode"] == 200
    assert result["body"] == ""
