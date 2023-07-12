INPUT = {
    "definitions": {},
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://example.com/object1660233148.json",
    "title": "Root",
    "type": "object",
    "required": ["instance_id", "region"],
    "properties": {
        "instance_id": {
            "$id": "#root/instance_id",
            "title": "Instance_id",
            "type": "string",
            "default": "",
            "examples": ["i-042dd005362091826"],
            "pattern": "^.*$",
        },
        "region": {
            "$id": "#root/region",
            "title": "Region",
            "type": "string",
            "default": "",
            "examples": ["us-east-1"],
            "pattern": "^.*$",
        },
    },
}
