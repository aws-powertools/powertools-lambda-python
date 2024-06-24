from aws_lambda_powertools.event_handler.openapi.swagger_ui.html import (
    generate_swagger_html,
)
from aws_lambda_powertools.event_handler.openapi.swagger_ui.oauth2 import (
    OAuth2Config,
    generate_oauth2_redirect_html,
)

__all__ = [
    "generate_swagger_html",
    "generate_oauth2_redirect_html",
    "OAuth2Config",
]
