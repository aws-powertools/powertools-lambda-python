"""
OpenAPI Schema Fix Example

This example demonstrates how the automatic OpenAPI schema fix works for UploadFile parameters.
The fix resolves missing component references that would otherwise cause validation errors
in tools like Swagger Editor.

IMPORTANT: As of this version, the fix is automatically applied by APIGatewayRestResolver.
This example shows how the fix works internally and is provided for educational purposes.

Example shows:
- Custom resolver that replicates the built-in fix functionality
- UploadFile usage with File parameters
- OpenAPI schema generation with proper component references
- How missing component references are detected and resolved

For production use, simply use APIGatewayRestResolver directly - the fix is automatically applied.
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
        missing_refs = self._find_missing_component_references(schema_dict)

        # If no missing references, return the original schema
        if not missing_refs:
            return schema

        # Add missing components to the schema
        self._add_missing_components(schema_dict, missing_refs)

        # Rebuild the schema with the added components
        return schema.__class__(**schema_dict)

    def _find_missing_component_references(self, schema_dict: dict) -> list[tuple[str, str]]:
        """Find all missing component references in multipart/form-data schemas."""
        missing_refs: list[tuple[str, str]] = []
        paths = schema_dict.get("paths", {})

        for path_item in paths.values():
            self._check_path_item_for_missing_refs(path_item, schema_dict, missing_refs)

        return missing_refs

    def _check_path_item_for_missing_refs(
        self,
        path_item: dict,
        schema_dict: dict,
        missing_refs: list[tuple[str, str]],
    ) -> None:
        """Check a single path item for missing component references."""
        for _method, operation in path_item.items():
            if not isinstance(operation, dict) or "requestBody" not in operation:
                continue

            self._check_operation_for_missing_refs(operation, schema_dict, missing_refs)

    def _check_operation_for_missing_refs(
        self,
        operation: dict,
        schema_dict: dict,
        missing_refs: list[tuple[str, str]],
    ) -> None:
        """Check a single operation for missing component references."""
        req_body = operation.get("requestBody", {})
        content = req_body.get("content", {})
        multipart = content.get("multipart/form-data", {})
        schema_ref = multipart.get("schema", {})

        if "$ref" in schema_ref:
            ref = schema_ref["$ref"]
            if ref.startswith("#/components/schemas/"):
                component_name = ref[len("#/components/schemas/") :]

                if self._is_component_missing(schema_dict, component_name):
                    missing_refs.append((component_name, ref))

    def _is_component_missing(self, schema_dict: dict, component_name: str) -> bool:
        """Check if a component is missing from the schema."""
        components = schema_dict.get("components", {})
        schemas = components.get("schemas", {})
        return component_name not in schemas

    def _add_missing_components(self, schema_dict: dict, missing_refs: list[tuple[str, str]]) -> None:
        """Add missing components to the schema."""
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
