INPUT = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "$id": "http://example.com/example.json",
    "type": "object",
    "title": "Sample schema",
    "description": "The root schema comprises the entire JSON document.",
    "examples": [{"username": "hello world", "password": "lessa", "ip": "192.168.0.1"}],
    "required": ["username", "password", "ip"],
    "properties": {
        "username": {
            "$id": "#/properties/username",
            "type": "string",
            "title": "The username",
            "examples": ["lambda"],
            "maxLength": 30,
        },
        "password": {
            "$id": "#/properties/password",
            "type": "string",
            "title": "The password",
            "examples": ["powertools"],
            "maxLength": 30,
        },
        "ip": {
            "$id": "#/properties/ip",
            "type": "string",
            "title": "The ip",
            "format": "ipv4",
            "examples": ["192.168.0.1"],
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
    "examples": [{"statusCode": 200, "body": {}}],
    "required": ["statusCode", "body"],
    "properties": {
        "statusCode": {
            "$id": "#/properties/statusCode",
            "type": "integer",
            "title": "The statusCode",
            "examples": [200],
            "maxLength": 3,
        },
        "body": {
            "$id": "#/properties/body",
            "type": "object",
            "title": "The body",
            "examples": [
                '{"ip": "192.168.0.1", "permissions": ["read", "write"], "user_id": "7576b683-295e-4f69-b558-70e789de1b18", "name": "Christopher Dunn"}'  # noqa E501
            ],
        },
    },
}
