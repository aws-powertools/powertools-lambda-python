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

    def test_upload_file_component_references_are_resolved(self):
        """Test that UploadFile component references are properly resolved in OpenAPI schema."""
        from aws_lambda_powertools.event_handler.openapi.params import fix_upload_file_schema_references

        # GIVEN a schema with missing component references (simulating the issue)
        mock_schema = {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "0.1.0"},
            "paths": {
                "/upload_with_metadata": {
                    "post": {
                        "summary": "Upload With Metadata",
                        "requestBody": {
                            "content": {
                                "multipart/form-data": {"schema": {"$ref": "#/components/schemas/TestUploadComponent"}},
                            },
                            "required": True,
                        },
                        "responses": {"200": {"description": "Successful Response"}},
                    },
                },
            },
            # Note: components section is missing, which is the problem our fix addresses
        }

        # WHEN we apply the fix
        fixed_schema = fix_upload_file_schema_references(mock_schema)

        # THEN the schema should have the correct components
        components = fixed_schema.get("components", {})
        schemas = components.get("schemas", {})

        # The component should now exist
        assert "TestUploadComponent" in schemas

        # Verify the component has the correct structure
        component = schemas["TestUploadComponent"]
        assert component["type"] == "object"
        assert "properties" in component
        assert "file" in component["properties"]
        assert component["properties"]["file"]["type"] == "string"
        assert component["properties"]["file"]["format"] == "binary"
        assert "required" in component
        assert "file" in component["required"]

    def test_upload_file_schema_fix_with_real_app(self):
        """Test that the schema fix works with a real application."""
        # GIVEN a real app with UploadFile
        app = self._create_test_app()

        # WHEN we generate the OpenAPI schema
        schema = app.get_openapi_schema()
        schema_dict = schema.model_dump(by_alias=True)

        # THEN all component references should be resolved
        from aws_lambda_powertools.event_handler.openapi.params import _find_missing_upload_file_components

        missing_components = _find_missing_upload_file_components(schema_dict)

        # No missing components should be found
        assert len(missing_components) == 0, f"Found missing components: {missing_components}"

        # Verify that components exist for UploadFile references
        paths = schema_dict.get("paths", {})
        components = schema_dict.get("components", {}).get("schemas", {})

        for path_data in paths.values():
            for operation in path_data.values():
                if not isinstance(operation, dict) or "requestBody" not in operation:
                    continue

                content = operation.get("requestBody", {}).get("content", {})
                multipart = content.get("multipart/form-data", {})
                schema_ref = multipart.get("schema", {})

                if "$ref" in schema_ref:
                    ref = schema_ref["$ref"]
                    if ref.startswith("#/components/schemas/"):
                        component_name = ref[len("#/components/schemas/") :]
                        assert component_name in components, f"Missing component: {component_name}"
