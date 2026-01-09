from aws_lambda_powertools.event_handler.openapi import OpenAPIMerge
from aws_lambda_powertools.event_handler.openapi.models import Contact, License, Server, Tag

merge = OpenAPIMerge(
    title="My API",
    version="1.0.0",
    summary="API summary",
    description="Full API description",
    terms_of_service="https://example.com/tos",
    contact=Contact(name="Support", email="support@example.com"),
    license_info=License(name="MIT"),
    servers=[Server(url="https://api.example.com")],
    tags=[Tag(name="users", description="User operations")],
    on_conflict="warn",
)

merge.discover(path="./src", pattern="**/handler.py", recursive=True)
schema = merge.get_openapi_json_schema()
