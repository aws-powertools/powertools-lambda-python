"""Test for bug #7711: OpenAPI schema return types bleed across routes when reusing response dictionaries"""

from __future__ import annotations

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse


class ExamSummary(BaseModel):
    """Summary information about an exam"""

    id: str
    name: str
    duration_minutes: int


class ExamConfig(BaseModel):
    """Detailed configuration for an exam"""

    id: str
    name: str
    duration_minutes: int
    max_attempts: int
    passing_score: int


class Responses:
    """Pre-configured OpenAPI response schemas."""

    # Base responses
    OK = {200: OpenAPIResponse(description="Successful operation")}
    NOT_FOUND = {404: OpenAPIResponse(description="Resource not found")}
    VALIDATION_ERROR = {422: OpenAPIResponse(description="Validation error")}
    SERVER_ERROR = {500: OpenAPIResponse(description="Internal server error")}

    # Common combinations
    STANDARD_ERRORS = {**NOT_FOUND, **VALIDATION_ERROR, **SERVER_ERROR}

    @classmethod
    def combine(cls, *response_dicts: dict[int, OpenAPIResponse]) -> dict[int, OpenAPIResponse]:
        """Combine multiple response dictionaries."""
        result = {}
        for response_dict in response_dicts:
            result.update(response_dict)
        return result


def test_openapi_shared_response_no_bleed():
    """
    Test that when reusing the same response dictionary across multiple routes,
    each route gets the correct return type in its OpenAPI schema.

    This reproduces bug #7711 where the schema from one route bleeds into another
    when they share the same response dictionary object.
    """
    app = APIGatewayRestResolver(enable_validation=True)

    @app.get(
        "/exams",
        tags=["Exams"],
        responses=Responses.combine(Responses.OK, Responses.STANDARD_ERRORS),
    )
    def list_exams() -> Response[list[ExamSummary]]:
        """Lists all available exams."""
        return Response(
            status_code=200,
            body=[
                ExamSummary(id="1", name="Math", duration_minutes=60),
                ExamSummary(id="2", name="Science", duration_minutes=90),
            ],
        )

    @app.get(
        "/exams/<exam_id>",
        tags=["Exams"],
        responses=Responses.combine(Responses.OK, Responses.STANDARD_ERRORS),  # Reusing the shared Responses.OK
    )
    def get_exam_config(exam_id: str) -> Response[ExamConfig]:
        """Get the configuration for a specific exam"""
        return Response(
            status_code=200,
            body=ExamConfig(
                id=exam_id,
                name="Math",
                duration_minutes=60,
                max_attempts=3,
                passing_score=70,
            ),
        )

    # Generate the OpenAPI schema
    schema = app.get_openapi_schema()

    # Verify /exams endpoint has the correct list[ExamSummary] schema
    exams_response = schema.paths["/exams"].get.responses[200]
    exams_schema = exams_response.content["application/json"].schema_

    # The schema should be an array type
    assert exams_schema.type == "array", f"/exams should return an array, got {exams_schema.type}"
    assert exams_schema.items is not None, "/exams should have items definition"

    # The items should reference ExamSummary
    if hasattr(exams_schema.items, "ref"):
        assert "ExamSummary" in exams_schema.items.ref, (
            f"/exams should return list[ExamSummary], got {exams_schema.items.ref}"
        )
    elif hasattr(exams_schema.items, "title"):
        assert exams_schema.items.title == "ExamSummary", (
            f"/exams should return list[ExamSummary], got {exams_schema.items.title}"
        )

    # Verify /exams/{exam_id} endpoint has the correct ExamConfig schema
    exam_detail_response = schema.paths["/exams/{exam_id}"].get.responses[200]
    exam_detail_schema = exam_detail_response.content["application/json"].schema_

    # The schema should NOT be an array - it should be an object
    assert exam_detail_schema.type != "array", "/exams/{exam_id} should not return an array (bug #7711 - schema bleed)"

    # The schema should reference ExamConfig
    if hasattr(exam_detail_schema, "ref"):
        assert "ExamConfig" in exam_detail_schema.ref, (
            f"/exams/{{exam_id}} should return ExamConfig, got {exam_detail_schema.ref}"
        )
    elif hasattr(exam_detail_schema, "title"):
        assert exam_detail_schema.title == "ExamConfig", (
            f"/exams/{{exam_id}} should return ExamConfig, got {exam_detail_schema.title}"
        )


def test_openapi_shared_response_dict_not_mutated():
    """
    Test that the original shared response dictionary is not mutated
    when generating OpenAPI schemas.
    """
    app = APIGatewayRestResolver(enable_validation=True)

    # Create a shared response dictionary
    shared_responses = Responses.combine(Responses.OK, Responses.STANDARD_ERRORS)

    # Store the original state - the 200 response should not have 'content' key
    original_200_response = shared_responses[200].copy()
    assert "content" not in original_200_response, "200 response should not have content initially"

    @app.get("/route1", responses=shared_responses)
    def route1() -> Response[ExamSummary]:
        return Response(
            status_code=200,
            body=ExamSummary(id="1", name="Test", duration_minutes=60),
        )

    @app.get("/route2", responses=shared_responses)
    def route2() -> Response[ExamConfig]:
        return Response(
            status_code=200,
            body=ExamConfig(
                id="1",
                name="Test",
                duration_minutes=60,
                max_attempts=3,
                passing_score=70,
            ),
        )

    # Generate the OpenAPI schema
    app.get_openapi_schema()

    # Verify the shared dictionary was not mutated
    # The original 200 response should still not have 'content' key
    assert "content" not in shared_responses[200], (
        "Shared response dictionary should not be mutated during OpenAPI schema generation (bug #7711)"
    )
