from typing import Any, Dict

import pytest
from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.parser import BaseEnvelope, ModelValidationError


@pytest.fixture
def dummy_event():
    return {"payload": {"message": "hello world"}}


@pytest.fixture
def dummy_schema():
    """Wanted payload structure"""

    class MyDummyModel(BaseModel):
        message: str

    return MyDummyModel


@pytest.fixture
def dummy_envelope_schema():
    """Event wrapper structure"""

    class MyDummyEnvelopeSchema(BaseModel):
        payload: Dict

    return MyDummyEnvelopeSchema


@pytest.fixture
def dummy_envelope(dummy_envelope_schema):
    class MyDummyEnvelope(BaseEnvelope):
        """Unwrap dummy event within payload key"""

        def parse(self, data: Dict[str, Any], model: BaseModel):
            try:
                parsed_enveloped = dummy_envelope_schema(**data)
            except (ValidationError, TypeError) as e:
                raise ModelValidationError("Dummy input does not conform with schema") from e
            return self._parse(data=parsed_enveloped.payload, model=model)

    return MyDummyEnvelope
