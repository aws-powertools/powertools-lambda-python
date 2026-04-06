from aws_lambda_powertools.event_handler.openapi import OpenAPIMerge

merge = OpenAPIMerge(title="API", version="1.0.0")

merge.discover(
    path="./src",
    pattern=["handler.py", "api.py", "*_routes.py"],
    recursive=True,
)
