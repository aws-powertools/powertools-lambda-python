"""Handler with tags for testing tag merging."""

from __future__ import annotations

from aws_lambda_powertools.event_handler import APIGatewayRestResolver

app = APIGatewayRestResolver()


@app.get("/tagged")
def tagged_endpoint():
    """Endpoint in tagged handler."""
    return {"tagged": True}


# Override get_openapi_schema to include tags
_original_get_openapi_schema = app.get_openapi_schema


def get_openapi_schema_with_tags(**kwargs):
    kwargs.setdefault("tags", ["handler-tag"])
    return _original_get_openapi_schema(**kwargs)


app.get_openapi_schema = get_openapi_schema_with_tags
