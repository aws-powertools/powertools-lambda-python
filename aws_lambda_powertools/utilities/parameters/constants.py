from __future__ import annotations

import base64
import json
from typing import Any, Literal

SSM_PARAMETER_TYPES = Literal["String", "StringList", "SecureString"]
SSM_PARAMETER_TIER = Literal["Standard", "Advanced", "Intelligent-Tiering"]

DEFAULT_MAX_AGE_SECS = "300"

# These providers will be dynamically initialized on first use of the helper functions
DEFAULT_PROVIDERS: dict[str, Any] = {}
TRANSFORM_METHOD_JSON = "json"
TRANSFORM_METHOD_BINARY = "binary"
TRANSFORM_METHOD_MAPPING = {
    TRANSFORM_METHOD_JSON: json.loads,
    TRANSFORM_METHOD_BINARY: base64.b64decode,
    ".json": json.loads,
    ".binary": base64.b64decode,
    None: lambda x: x,
}
