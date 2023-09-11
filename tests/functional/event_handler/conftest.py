import json

import pytest


@pytest.fixture
def json_dump():
    # our serializers reduce length to save on costs; fixture to replicate separators
    return lambda obj: json.dumps(obj, separators=(",", ":"))


@pytest.fixture
def validation_schema():
    return {
        "$schema": "https://json-schema.org/draft-07/schema",
        "$id": "https://example.com/example.json",
        "type": "object",
        "title": "Sample schema",
        "description": "The root schema comprises the entire JSON document.",
        "examples": [{"message": "hello world", "username": "lessa"}],
        "required": ["message", "username"],
        "properties": {
            "message": {
                "$id": "#/properties/message",
                "type": "string",
                "title": "The message",
                "examples": ["hello world"],
            },
            "username": {
                "$id": "#/properties/username",
                "type": "string",
                "title": "The username",
                "examples": ["lessa"],
            },
        },
    }


@pytest.fixture
def raw_event():
    return {"message": "hello hello", "username": "blah blah"}
