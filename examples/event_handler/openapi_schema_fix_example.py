"""
OpenAPI Schema Fix Example

This example demonstrates how the automatic OpenAPI schema fix works for UploadFile parameters.
The fix resolves missing component references that would otherwise cause validation errors
in tools like Swagger Editor.

Example shows:
- Custom resolver that demonstrates the fix (though it's now built-in)
- UploadFile usage with File parameters
- OpenAPI schema generation with proper component references
"""

from __future__ import annotations

import json

from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, Form, UploadFile


class EnumEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle enum values."""

    def default(self, obj):
        """Convert enum to string."""
        if hasattr(obj, "value") and not callable(obj.value):
            return obj.value
        return super().default(obj)


class OpenAPISchemaFixResolver(APIGatewayRestResolver):
    """
    A custom resolver that demonstrates the OpenAPI schema fix for UploadFile parameters.

    NOTE: This fix is now built into the main APIGatewayRestResolver, so this example
    is primarily for educational purposes to show how the fix works.

    The issue that was fixed: when using UploadFile with File parameters, the OpenAPI schema
    would reference components that didn't exist in the components/schemas section.
    """

    def get_openapi_schema(self, **kwargs):
        """Override the get_openapi_schema method to add missing UploadFile components."""
        # Get the original schema
        schema = super().get_openapi_schema(**kwargs)
        schema_dict = schema.model_dump(by_alias=True)

        # Find all multipart/form-data references that might be missing
        missing_refs = []
        paths = schema_dict.get("paths", {})
        for path_item in paths.values():
            for _method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue

                if "requestBody" not in operation:
                    continue

                req_body = operation.get("requestBody", {})
                content = req_body.get("content", {})
                multipart = content.get("multipart/form-data", {})
                schema_ref = multipart.get("schema", {})

                if "$ref" in schema_ref:
                    ref = schema_ref["$ref"]
                    if ref.startswith("#/components/schemas/"):
                        component_name = ref[len("#/components/schemas/") :]

                        # Check if the component exists
                        components = schema_dict.get("components", {})
                        schemas = components.get("schemas", {})

                        if component_name not in schemas:
                            missing_refs.append((component_name, ref))

        # If no missing references, return the original schema
        if not missing_refs:
            return schema

        # Add missing components to the schema
        components = schema_dict.setdefault("components", {})
        schemas = components.setdefault("schemas", {})

        for component_name, _ref in missing_refs:
            # Create a schema for the missing component
            # This is a simple multipart form-data schema with file properties
            schemas[component_name] = {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary", "description": "File to upload"},
                    # Add other properties that might be in the form
                    "description": {"type": "string", "default": "No description provided"},
                    "tags": {"type": "string", "nullable": True},
                },
                "required": ["file"],
            }

        # Rebuild the schema with the added components
        return schema.__class__(**schema_dict)


def create_test_app():
    """Create a test app with the fixed resolver."""
    app = OpenAPISchemaFixResolver()

    @app.post("/upload-with-metadata")
    def upload_file_with_metadata(
        file: Annotated[UploadFile, File(description="File to upload")],
        description: Annotated[str, Form()] = "No description provided",
        tags: Annotated[str | None, Form()] = None,
    ):
        """Upload a file with additional metadata."""
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file.size,
            "description": description,
            "tags": tags or [],
        }

    return app


def main():
    """Test the fix."""
    app = create_test_app()
    schema = app.get_openapi_schema()
    schema_dict = schema.model_dump(by_alias=True)
    return schema_dict


if __name__ == "__main__":
    main()
