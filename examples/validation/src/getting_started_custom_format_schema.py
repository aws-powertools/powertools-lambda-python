INPUT = {
    "definitions": {},
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://example.com/object1660245931.json",
    "title": "Root",
    "type": "object",
    "required": ["accountid", "region"],
    "properties": {
        "accountid": {
            "$id": "#root/accountid",
            "title": "The accountid",
            "type": "string",
            "format": "awsaccountid",
            "default": "",
            "examples": ["123456789012"],
        },
        "region": {
            "$id": "#root/region",
            "title": "The region",
            "type": "string",
            "default": "",
            "examples": ["us-east-1"],
            "pattern": "^.*$",
        },
    },
}
