from __future__ import annotations

from pydantic import BaseModel, Field

from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
)


class Todo(BaseModel):
    id: int = Field(examples=[1])
    title: str = Field(examples=["Example 1"])
    priority: float = Field(examples=[0.5])
    completed: bool = Field(examples=[True])


app = APIGatewayRestResolver(enable_validation=True)


@app.get("/openapi_schema_with_pep563")
def openapi_schema():
    return app.get_openapi_json_schema(
        title="Powertools e2e API",
        version="1.0.0",
        description="This is a sample Powertools e2e API",
        openapi_extensions={"x-amazon-apigateway-gateway-responses": {"DEFAULT_4XX"}},
    )


@app.get("/")
def handler() -> Todo:
    return Todo(id=0, title="", priority=0.0, completed=False)


def lambda_handler(event, context):
    return app.resolve(event, context)
