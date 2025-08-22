import pytest
import json
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile


class TestUploadFileOpenAPISchema:
    """Test UploadFile OpenAPI schema generation."""

    def test_upload_file_openapi_schema(self):
        """Test OpenAPI schema generation with UploadFile."""
        app = APIGatewayRestResolver()

        @app.post("/upload-single")
        def upload_single_file(file: Annotated[UploadFile, File()]):
            """Upload a single file."""
            return {"filename": file.filename, "size": file.size}

        @app.post("/upload-multiple")
        def upload_multiple_files(
            primary_file: Annotated[UploadFile, File(alias="primary", description="Primary file with metadata")],
            secondary_file: Annotated[bytes, File(alias="secondary", description="Secondary file as bytes")],
        ):
            """Upload multiple files - showcasing BOTH UploadFile and bytes approaches."""
            return {
                "status": "uploaded",
                "primary_filename": primary_file.filename,
                "primary_content_type": primary_file.content_type,
                "primary_size": primary_file.size,
                "secondary_size": len(secondary_file),
                "total_size": primary_file.size + len(secondary_file),
            }

        # Generate OpenAPI schema
        schema = app.get_openapi_schema()
        
        # Print schema for debugging
        schema_dict = schema.model_dump()
        print("SCHEMA PATHS:")
        for path, path_item in schema_dict["paths"].items():
            print(f"Path: {path}")
            if "post" in path_item:
                if "requestBody" in path_item["post"]:
                    if "content" in path_item["post"]["requestBody"]:
                        if "multipart/form-data" in path_item["post"]["requestBody"]["content"]:
                            print("  Found multipart/form-data")
                            print(f"  Schema: {json.dumps(path_item['post']['requestBody']['content']['multipart/form-data'], indent=2)}")
        
        print("\nSCHEMA COMPONENTS:")
        if "components" in schema_dict and "schemas" in schema_dict["components"]:
            for name, comp_schema in schema_dict["components"]["schemas"].items():
                if "file" in name.lower() or "upload" in name.lower():
                    print(f"Component: {name}")
                    print(f"  {json.dumps(comp_schema, indent=2)}")
        
        # Basic verification
        paths = schema.paths
        assert "/upload-single" in paths
        assert "/upload-multiple" in paths
        
        # Verify upload-single endpoint exists
        upload_single = paths["/upload-single"]
        assert upload_single.post is not None
        
        # Verify upload-multiple endpoint exists
        upload_multiple = paths["/upload-multiple"]
        assert upload_multiple.post is not None
        
        # Print success
        print("\n✅ Basic OpenAPI schema generation tests passed")
