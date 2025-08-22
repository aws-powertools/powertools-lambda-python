import json

from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile


class TestUploadFileOpenAPISchema:
    """Test UploadFile OpenAPI schema generation."""

    def _create_test_app(self):
        """Create test application with upload endpoints."""
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

        return app

    def _print_multipart_schemas(self, schema_dict):
        """Print multipart form data schemas from paths."""
        print("SCHEMA PATHS:")
        for path, path_item in schema_dict["paths"].items():
            print(f"Path: {path}")

            # Merged nested if statements
            if (
                "post" in path_item
                and "requestBody" in path_item["post"]
                and "content" in path_item["post"]["requestBody"]
                and "multipart/form-data" in path_item["post"]["requestBody"]["content"]
            ):
                print("  Found multipart/form-data")
                content = path_item["post"]["requestBody"]["content"]["multipart/form-data"]
                print(f"  Schema: {json.dumps(content, indent=2)}")

    def _print_file_components(self, schema_dict):
        """Print file-related components from schema."""
        print("\nSCHEMA COMPONENTS:")
        components = schema_dict.get("components", {})
        schemas = components.get("schemas", {})

        for name, comp_schema in schemas.items():
            if "file" in name.lower() or "upload" in name.lower():
                print(f"Component: {name}")
                print(f"  {json.dumps(comp_schema, indent=2)}")

    def test_upload_file_openapi_schema(self):
        """Test OpenAPI schema generation with UploadFile."""
        # Setup test app with file upload endpoints
        app = self._create_test_app()

        # Generate OpenAPI schema
        schema = app.get_openapi_schema()
        schema_dict = schema.model_dump()

        # Print debug information (optional)
        self._print_multipart_schemas(schema_dict)
        self._print_file_components(schema_dict)

        # Basic verification
        paths = schema.paths
        assert "/upload-single" in paths
        assert "/upload-multiple" in paths
        assert paths["/upload-single"].post is not None
        assert paths["/upload-multiple"].post is not None

        # Print success
        print("\n✅ Basic OpenAPI schema generation tests passed")
