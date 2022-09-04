INPUT = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "$id": "http://example.com/example.json",
    "type": "object",
    "title": "Sample schema",
    "description": "The root schema comprises the entire JSON document.",
    "examples": [{"user_id": "0d44b083-8206-4a3a-aa95-5d392a99be4a", "project": "powertools", "ip": "192.168.0.1"}],
    "required": ["user_id", "project", "ip"],
    "properties": {
        "user_id": {
            "$id": "#/properties/user_id",
            "type": "string",
            "title": "The user_id",
            "examples": ["0d44b083-8206-4a3a-aa95-5d392a99be4a"],
            "maxLength": 50,
        },
        "project": {
            "$id": "#/properties/project",
            "type": "string",
            "title": "The project",
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
                '{"ip": "192.168.0.1", "permissions": ["read", "write"], "user_id": "7576b683-295e-4f69-b558-70e789de1b18", "name": "Project Lambda Powertools"}'  # noqa E501
            ],
        },
    },
}
