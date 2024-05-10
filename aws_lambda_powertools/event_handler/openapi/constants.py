from pydantic import ConfigDict

DEFAULT_API_VERSION = "1.0.0"
DEFAULT_OPENAPI_VERSION = "3.1.0"
MODEL_CONFIG_ALLOW = ConfigDict(extra="allow")
MODEL_CONFIG_IGNORE = ConfigDict(extra="ignore")
