from aws_lambda_powertools.event_handler import LambdaFunctionUrlResolver, Response, content_types
from aws_lambda_powertools.utilities.data_classes import LambdaFunctionUrlEvent
from tests.functional.utils import load_event


def test_lambda_function_url_event():
    # GIVEN a Lambda Function Url type event
    app = LambdaFunctionUrlResolver()

    @app.post("/my/path")
    def foo():
        assert isinstance(app.current_event, LambdaFunctionUrlEvent)
        assert app.lambda_context == {}
        assert app.current_event.request_context.stage is not None
        return Response(200, content_types.TEXT_HTML, "foo")

    # WHEN calling the event handler
    result = app(load_event("lambdaFunctionUrlIAMEvent.json"), {})

    # THEN process event correctly
    # AND set the current_event type as LambdaFunctionUrlEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == content_types.TEXT_HTML
    assert "Cookies" not in result["headers"]
    assert result["body"] == "foo"


def test_lambda_function_url_event_with_cookies():
    # GIVEN a Lambda Function Url type event
    app = LambdaFunctionUrlResolver()

    @app.post("/my/path")
    def foo():
        assert isinstance(app.current_event, LambdaFunctionUrlEvent)
        assert app.lambda_context == {}
        return Response(200, content_types.TEXT_PLAIN, "foo", cookies=["CookieMonster"])

    # WHEN calling the event handler
    result = app(load_event("lambdaFunctionUrlEvent.json"), {})

    # THEN process event correctly
    # AND set the current_event type as LambdaFunctionUrlEvent
    assert result["statusCode"] == 200
    assert result["headers"]["Cookies"] == ["CookieMonster"]


def test_lambda_function_url_no_matches():
    # GIVEN a Lambda Function Url type event
    app = LambdaFunctionUrlResolver()

    @app.post("/no_match")
    def foo():
        raise RuntimeError()

    # WHEN calling the event handler
    result = app(load_event("lambdaFunctionUrlIAMEvent.json"), {})

    # THEN process event correctly
    # AND return 404 because the event doesn't match any known route
    assert result["statusCode"] == 404
