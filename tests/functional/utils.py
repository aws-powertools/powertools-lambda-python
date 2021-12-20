import base64
import json
from pathlib import Path
from typing import Any


def load_event(file_name: str) -> Any:
    path = Path(str(Path(__file__).parent.parent) + "/events/" + file_name)
    return json.loads(path.read_text())


def str_to_b64(data: str) -> str:
    return base64.b64encode(data.encode()).decode("utf-8")


def b64_to_str(data: str) -> str:
    return base64.b64decode(data.encode()).decode("utf-8")
