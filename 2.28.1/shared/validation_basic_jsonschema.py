INPUT = {
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
            "maxLength": 100,
        },
        "username": {
            "$id": "#/properties/username",
            "type": "string",
            "title": "The username",
            "examples": ["lessa"],
            "maxLength": 30,
        },
    },
}

OUTPUT = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "$id": "http://example.com/example.json",
    "type": "object",
    "title": "Sample outgoing schema",
    "description": "The root schema comprises the entire JSON document.",
    "examples": [{"statusCode": 200, "body": "response"}],
    "required": ["statusCode", "body"],
    "properties": {
        "statusCode": {"$id": "#/properties/statusCode", "type": "integer", "title": "The statusCode"},
        "body": {"$id": "#/properties/body", "type": "string", "title": "The response"},
    },
}
