INPUT = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "$id": "http://example.com/example.json",
    "type": "object",
    "title": "Sample schema",
    "description": "The root schema comprises the entire JSON document.",
    "examples": [{"user_id": "0d44b083-8206-4a3a-aa95-5d392a99be4a", "powertools": "lessa", "ip": "192.168.0.1"}],
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
