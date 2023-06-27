INPUT = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "$id": "http://example.com/example.json",
    "type": "object",
    "title": "Sample schema",
    "description": "The root schema comprises the entire JSON document.",
    "examples": [
        {
            "owner": "123456789012",
            "logGroup": "/aws/lambda/powertools-example",
            "logStream": "2022/08/07/[$LATEST]d3a8dcaffc7f4de2b8db132e3e106660",
            "logEvents": {},
        },
    ],
    "required": ["owner", "logGroup", "logStream", "logEvents"],
    "properties": {
        "owner": {
            "$id": "#/properties/owner",
            "type": "string",
            "title": "The owner",
            "examples": ["123456789012"],
            "maxLength": 12,
        },
        "logGroup": {
            "$id": "#/properties/logGroup",
            "type": "string",
            "title": "The logGroup",
            "examples": ["/aws/lambda/powertools-example"],
            "maxLength": 100,
        },
        "logStream": {
            "$id": "#/properties/logStream",
            "type": "string",
            "title": "The logGroup",
            "examples": ["2022/08/07/[$LATEST]d3a8dcaffc7f4de2b8db132e3e106660"],
            "maxLength": 100,
        },
        "logEvents": {
            "$id": "#/properties/logEvents",
            "type": "array",
            "title": "The logEvents",
            "examples": [
                "{'id': 'eventId1', 'message': {'username': 'lessa', 'message': 'hello world'}, 'timestamp': 1440442987000}"  # noqa E501
            ],
        },
    },
}
