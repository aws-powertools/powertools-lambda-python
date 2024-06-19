PARENT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://example.com/schemas/parent.json",
    "type": "object",
    "properties": {
        "ParentSchema": {
            "$ref": "https://SCHEMA",
        },
    },
}

CHILD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://example.com/schemas/child.json",
    "type": "object",
    "properties": {
        "project": {
            "type": "string",
        },
    },
    "required": ["project"],
}
