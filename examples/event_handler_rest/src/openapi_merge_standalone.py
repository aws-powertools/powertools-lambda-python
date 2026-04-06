from pathlib import Path

from aws_lambda_powertools.event_handler.openapi import OpenAPIMerge

merge = OpenAPIMerge(
    title="My Unified API",
    version="1.0.0",
    description="Consolidated API from multiple Lambda functions",
)

# Discover handlers
merge.discover(
    path="./src/functions",
    pattern="*_handler.py",
    recursive=True,
)

# Generate schema
schema_json = merge.get_openapi_json_schema()

# Write to file
output = Path("openapi.json")
output.write_text(schema_json)
