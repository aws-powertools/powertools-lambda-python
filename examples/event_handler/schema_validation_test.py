#!/usr/bin/env python3
"""
OpenAPI Schema Validation Test

This script tests OpenAPI schema generation with UploadFile to ensure proper validation.
It creates a schema and saves it to a temporary file for external validation tools
like Swagger Editor.

The test demonstrates:
- UploadFile endpoint creation
- OpenAPI schema generation
- Schema output for external validation
"""

from __future__ import annotations

import json
import tempfile

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


def create_test_app():
    """Create a test app with UploadFile endpoints."""
    app = APIGatewayRestResolver()

    @app.post("/upload")
    def upload_file(file: Annotated[UploadFile, File()]):
        """Upload a file endpoint."""
        return {"filename": file.filename}

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
    """Generate and save OpenAPI schema for validation."""
    # Create a sample app with upload endpoints
    app = create_test_app()

    # Generate the OpenAPI schema (now includes automatic fix)
    schema = app.get_openapi_schema()
    schema_dict = schema.model_dump(by_alias=True)

    # Create a file for external validation (e.g., Swagger Editor)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        json.dump(schema_dict, tmp, cls=EnumEncoder, indent=2)
        print(f"Schema saved to: {tmp.name}")
        return tmp.name


if __name__ == "__main__":
    main()
