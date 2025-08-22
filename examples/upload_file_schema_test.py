#!/usr/bin/env python3
"""
Test script to diagnose OpenAPI schema issues with UploadFile.
"""

from __future__ import annotations

import json
import tempfile

from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile


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
    def upload_file(file: UploadFile):
        """Upload a file endpoint."""
        return {"filename": file.filename}
    
    @app.post("/upload-with-metadata")
    def upload_file_with_metadata(
        file: Annotated[UploadFile, File(description="File to upload")],
        description: str = "No description provided",
        tags: str = None,
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
    """Test the schema generation."""
    # Create a sample app with upload endpoints
    app = create_test_app()
    
    # Generate the OpenAPI schema
    schema = app.get_openapi_schema()
    schema_dict = schema.model_dump(by_alias=True)
    
    # Create a file for external validation
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        json.dump(schema_dict, tmp, cls=EnumEncoder, indent=2)
        return tmp.name


if __name__ == "__main__":
    main()
