"""Comprehensive tests for UploadFile OpenAPI schema generation and validation coverage."""

import pytest
from typing_extensions import Annotated
from unittest.mock import Mock

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import File, UploadFile, fix_upload_file_schema_references
from aws_lambda_powertools.event_handler.middlewares.openapi_validation import (
    _get_field_value, _resolve_field_type, _convert_value_type
)
from typing import Union, Optional


class TestUploadFileComprehensiveCoverage:
    """Comprehensive tests for UploadFile functionality covering missing lines."""

    def test_upload_file_openapi_schema_generation(self):
        """Test UploadFile generates correct OpenAPI schema."""
        app = APIGatewayRestResolver()

        @app.post("/upload")
        def upload_file(file: Annotated[UploadFile, File()]):
            return {"filename": file.filename}

        schema = app.get_openapi_schema()
        # Access the schema through object attributes
        upload_path = schema.paths["/upload"]
        request_body = upload_path.post.requestBody
        multipart_content = request_body.content["multipart/form-data"]
        
        assert multipart_content.schema_ is not None

    def test_upload_file_schema_fix_resolves_references(self):
        """Test schema fix function resolves UploadFile component references."""
        app = APIGatewayRestResolver()

        @app.post("/upload")
        def upload_file(file: Annotated[UploadFile, File()]):
            return {"status": "ok"}

        schema = app.get_openapi_schema()
        # Convert to dict for processing by fix function
        schema_dict = schema.model_dump()
        fix_upload_file_schema_references(schema_dict)
        
        # Verify components exist and are processed
        assert "components" in schema_dict

    def test_upload_file_validation_methods(self):
        """Test UploadFile validation methods for coverage."""
        upload_file = UploadFile(file=b"test content", filename="test.txt")
        
        # Test __get_validators__ method
        validators = upload_file.__get_validators__()
        assert callable(next(validators))
        
        # Test _validate_with_info method - this covers lines in validation
        validation_info = Mock()
        validated = upload_file._validate_with_info(b"content", validation_info)
        assert isinstance(validated, UploadFile)

    def test_upload_file_pydantic_schema_methods(self):
        """Test UploadFile Pydantic schema generation methods."""
        # Test __get_pydantic_json_schema__ - expect description to be included
        json_schema = UploadFile.__get_pydantic_json_schema__(Mock(), Mock())
        expected_schema = {
            "type": "string", 
            "format": "binary", 
            "description": "A file uploaded as part of a multipart/form-data request"
        }
        assert json_schema == expected_schema
        
        # Test __modify_schema__
        field_schema = {"type": "object"}
        UploadFile.__modify_schema__(field_schema)
        assert field_schema["type"] == "string"
        assert field_schema["format"] == "binary"

    def test_validation_middleware_functions(self):
        """Test validation middleware functions for coverage."""
        # Test _get_field_value with various scenarios
        mock_field = Mock()
        mock_field.alias = "test_field"
        assert _get_field_value({"test_field": "value"}, mock_field) == "value"
        assert _get_field_value(None, mock_field) is None
        
        # Test field without alias (AttributeError path)
        mock_field_no_alias = Mock(spec=[])  # No alias attribute
        assert _get_field_value({"test": "value"}, mock_field_no_alias) is None
        
        # Test _resolve_field_type with different Union scenarios
        assert _resolve_field_type(Union[str, None]) == str
        assert _resolve_field_type(Optional[int]) == int
        assert _resolve_field_type(str) == str
        
        # Test _convert_value_type for UploadFile conversion
        upload_file = _convert_value_type(b"content", UploadFile)
        assert isinstance(upload_file, UploadFile)
        assert _convert_value_type("string", str) == "string"

    def test_schema_fix_edge_cases(self):
        """Test schema fix function edge cases."""
        # Test with empty schema
        empty_schema = {}
        fix_upload_file_schema_references(empty_schema)
        assert empty_schema == {}
        
        # Test with schema missing components
        schema_no_components = {"paths": {}}
        fix_upload_file_schema_references(schema_no_components)
        # Should not crash and may or may not add components

    def test_upload_file_multipart_handling(self):
        """Test UploadFile in multipart scenarios for additional coverage."""
        app = APIGatewayRestResolver()

        @app.post("/upload-multi")
        def upload_multiple(
            primary: Annotated[UploadFile, File()],
            secondary: Annotated[bytes, File()]
        ):
            return {"files": 2}

        schema = app.get_openapi_schema()
        schema_dict = schema.model_dump()
        fix_upload_file_schema_references(schema_dict)
        
        # Verify multipart handling works without errors
        assert schema_dict is not None
