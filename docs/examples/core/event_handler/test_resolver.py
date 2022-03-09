import json
from pathlib import Path

import pytest
from src.index import app  # import the instance of AppSyncResolver from your code


def test_direct_resolver():
    # Load mock event from a file
    json_file_path = Path("appSyncDirectResolver.json")
    with open(json_file_path) as json_file:
        mock_event = json.load(json_file)

    # Call the implicit handler
    result = app(mock_event, {})

    assert result == "created this value"
