import json

import pytest


@pytest.fixture
def json_dump():
    # our serializers reduce length to save on costs; fixture to replicate separators
    return lambda obj: json.dumps(obj, separators=(",", ":"))
