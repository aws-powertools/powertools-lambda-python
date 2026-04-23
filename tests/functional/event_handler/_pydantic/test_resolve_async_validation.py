import asyncio

from aws_lambda_powertools.event_handler.api_gateway import (
    APIGatewayHttpResolver,
    BaseRouter,
)
from tests.functional.utils import load_event

API_RESTV2_EVENT = load_event("apiGatewayProxyV2Event_GET.json")


def _setup_app(app, event):
    BaseRouter.current_event = app._to_proxy_event(event)
    BaseRouter.lambda_context = {}


class TestResolveAsyncValidation:
    def test_validation_middleware_created_and_used(self):
        # GIVEN a resolver with validation enabled and an async handler
        app = APIGatewayHttpResolver(enable_validation=True)

        @app.get("/my/path")
        async def get_lambda() -> dict:
            await asyncio.sleep(0)
            return {"message": "validated"}

        # WHEN calling _resolve_async
        _setup_app(app, API_RESTV2_EVENT)
        result = asyncio.run(app._resolve_async())

        # THEN the validation middlewares are created and the response is valid
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 200
        assert hasattr(app, "_request_validation_middleware")
        assert hasattr(app, "_response_validation_middleware")

    def test_validation_middleware_lazy_created_for_per_route_validation(self):
        # GIVEN a resolver WITHOUT global validation, but a route WITH enable_validation=True
        app = APIGatewayHttpResolver()
        assert not hasattr(app, "_request_validation_middleware")

        @app.get("/my/path", enable_validation=True)
        async def get_lambda() -> dict:
            await asyncio.sleep(0)
            return {"message": "lazy validated"}

        # WHEN calling _resolve_async (triggers lazy creation in Route.call_async)
        _setup_app(app, API_RESTV2_EVENT)
        result = asyncio.run(app._resolve_async())

        # THEN validation middlewares are lazily created on the app
        response = result.build(app.current_event, app._cors)
        assert response["statusCode"] == 200
        assert hasattr(app, "_request_validation_middleware")
        assert hasattr(app, "_response_validation_middleware")
