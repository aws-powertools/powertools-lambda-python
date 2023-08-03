from typing import Callable, Optional

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, CORSConfig, Response


class CORSMiddleware:
    def __init__(self, config: Optional[CORSConfig] = None):
        self.cors = config or CORSConfig()

    def __call__(self, app: ApiGatewayResolver, get_response: Callable, **kwargs) -> Response:
        # Modify request details here before calling handler

        # Call Handler and get response
        result: Response = get_response(app, **kwargs)

        # Modify Response from Handler here before returning
        result.headers.update(self.cors.to_dict(app.current_event.get_header_value("Origin")))

        return result
