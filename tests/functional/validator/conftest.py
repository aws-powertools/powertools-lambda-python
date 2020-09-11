import json

import pytest


@pytest.fixture
def schema():
    return {
        "$schema": "http://json-schema.org/draft-07/schema",
        "$id": "http://example.com/example.json",
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


@pytest.fixture
def wrapped_event():
    return {"data": {"payload": {"message": "hello hello", "username": "blah blah"}}}


@pytest.fixture
def wrapped_event_json_string():
    return {"data": json.dumps({"payload": {"message": "hello hello", "username": "blah blah"}})}


@pytest.fixture
def wrapped_event_base64_json_string():
    return {"data": "eyJtZXNzYWdlIjogImhlbGxvIGhlbGxvIiwgInVzZXJuYW1lIjogImJsYWggYmxhaCJ9="}
