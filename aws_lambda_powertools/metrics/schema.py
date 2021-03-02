# flake8: noqa
CLOUDWATCH_EMF_SCHEMA = {
    "properties": {
        "_aws": {
            "$id": "#/properties/_aws",
            "properties": {
                "CloudWatchMetrics": {
                    "$id": "#/properties/_aws/properties/CloudWatchMetrics",
                    "items": {
                        "$id": "#/properties/_aws/properties/CloudWatchMetrics/items",
                        "properties": {
                            "Dimensions": {
                                "$id": "#/properties/_aws/properties/CloudWatchMetrics/items/properties/Dimensions",
                                "items": {
                                    "$id": "#/properties/_aws/properties/CloudWatchMetrics/items/properties/Dimensions/items",
                                    "items": {
                                        "$id": "#/properties/_aws/properties/CloudWatchMetrics/items/properties/Dimensions/items/items",
                                        "examples": ["Operation"],
                                        "minItems": 1,
                                        "pattern": "^(.*)$",
                                        "title": "DimensionReference",
                                        "type": "string",
                                    },
                                    "maxItems": 9,
                                    "minItems": 1,
                                    "title": "DimensionSet",
                                    "type": "array",
                                },
                                "minItems": 1,
                                "title": "The " "Dimensions " "Schema",
                                "type": "array",
                            },
                            "Metrics": {
                                "$id": "#/properties/_aws/properties/CloudWatchMetrics/items/properties/Metrics",
                                "items": {
                                    "$id": "#/properties/_aws/properties/CloudWatchMetrics/items/properties/Metrics/items",
                                    "minItems": 1,
                                    "properties": {
                                        "Name": {
                                            "$id": "#/properties/_aws/properties/CloudWatchMetrics/items/properties/Metrics/items/properties/Name",
                                            "examples": ["ProcessingLatency"],
                                            "minLength": 1,
                                            "pattern": "^(.*)$",
                                            "title": "MetricName",
                                            "type": "string",
                                        },
                                        "Unit": {
                                            "$id": "#/properties/_aws/properties/CloudWatchMetrics/items/properties/Metrics/items/properties/Unit",
                                            "examples": ["Milliseconds"],
                                            "pattern": "^(Seconds|Microseconds|Milliseconds|Bytes|Kilobytes|Megabytes|Gigabytes|Terabytes|Bits|Kilobits|Megabits|Gigabits|Terabits|Percent|Count|Bytes\\/Second|Kilobytes\\/Second|Megabytes\\/Second|Gigabytes\\/Second|Terabytes\\/Second|Bits\\/Second|Kilobits\\/Second|Megabits\\/Second|Gigabits\\/Second|Terabits\\/Second|Count\\/Second|None)$",
                                            "title": "MetricUnit",
                                            "type": "string",
                                        },
                                    },
                                    "required": ["Name"],
                                    "title": "MetricDefinition",
                                    "type": "object",
                                },
                                "minItems": 1,
                                "title": "MetricDefinitions",
                                "type": "array",
                            },
                            "Namespace": {
                                "$id": "#/properties/_aws/properties/CloudWatchMetrics/items/properties/Namespace",
                                "examples": ["MyApp"],
                                "minLength": 1,
                                "pattern": "^(.*)$",
                                "title": "CloudWatch " "Metrics " "Namespace",
                                "type": "string",
                            },
                        },
                        "required": ["Namespace", "Dimensions", "Metrics"],
                        "title": "MetricDirective",
                        "type": "object",
                    },
                    "title": "MetricDirectives",
                    "type": "array",
                },
                "Timestamp": {
                    "$id": "#/properties/_aws/properties/Timestamp",
                    "examples": [1565375354953],
                    "title": "The Timestamp " "Schema",
                    "type": "integer",
                },
            },
            "required": ["Timestamp", "CloudWatchMetrics"],
            "title": "Metadata",
            "type": "object",
        }
    },
    "required": ["_aws"],
    "title": "Root Node",
    "type": "object",
}
