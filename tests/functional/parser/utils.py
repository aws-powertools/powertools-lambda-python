import json
import os
from typing import Any


def get_event_file_path(file_name: str) -> str:
    return os.path.dirname(os.path.realpath(__file__)) + "/../../events/" + file_name


def load_event(file_name: str) -> Any:
    full_file_name = get_event_file_path(file_name)
    with open(full_file_name) as fp:
        return json.load(fp)
