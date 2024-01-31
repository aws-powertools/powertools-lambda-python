INPUT = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://example.com/object1661012141.json",
    "title": "Root",
    "type": "object",
    "required": ["headers"],
    "properties": {
        "headers": {
            "$id": "#root/headers",
            "title": "Headers",
            "type": "object",
            "required": ["X-Customer-Id"],
            "properties": {
                "X-Customer-Id": {
                    "$id": "#root/headers/X-Customer-Id",
                    "title": "X-customer-id",
                    "type": "string",
                    "default": "",
                    "examples": ["1"],
                    "pattern": "^.*$",
                },
            },
        },
    },
}
