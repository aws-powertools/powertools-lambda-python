from aws_lambda_powertools.event_handler.openapi.pydantic_loader import PYDANTIC_V2

DEFAULT_API_VERSION = "1.0.0"

if PYDANTIC_V2:
    DEFAULT_OPENAPI_VERSION = "3.1.0"
else:
    DEFAULT_OPENAPI_VERSION = "3.0.3"
