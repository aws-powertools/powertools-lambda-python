from aws_lambda_powertools.event_handler.openapi import OpenAPIMerge

merge = OpenAPIMerge(
    title="API",
    version="1.0.0",
    on_conflict="error",  # Raise OpenAPIMergeError on conflicts
)

merge.discover(path="./src", pattern="**/handler.py")
