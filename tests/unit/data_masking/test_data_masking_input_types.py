import dataclasses
import pytest
from pydantic import BaseModel

from aws_lambda_powertools.utilities.data_masking.base import DataMasking
from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING

@pytest.fixture
def data_masker() -> DataMasking:
    return DataMasking()

# ---------------------------
# Test with a Pydantic model
# ---------------------------
class MyPydanticModel(BaseModel):
    name: str
    age: int

def test_erase_on_pydantic_model(data_masker):
    # GIVEN a Pydantic model instance
    model_instance = MyPydanticModel(name="powertools", age=5)
    
    # WHEN calling erase with fields=["age"]
    result = data_masker.erase(model_instance, fields=["age"])
    
    # THEN the result should be a dict with the "age" field masked
    assert isinstance(result, dict)
    assert result["age"] == DATA_MASKING_STRING
    assert result["name"] == "powertools"


# ---------------------------
# Test with a dataclass
# ---------------------------
@dataclasses.dataclass
class MyDataClass:
    name: str
    age: int

def test_erase_on_dataclass(data_masker):
    # GIVEN a dataclass instance
    dc_instance = MyDataClass(name="powertools", age=5)
    
    # WHEN calling erase with fields=["age"]
    result = data_masker.erase(dc_instance, fields=["age"])
    
    # THEN the result should be a dict with the "age" field masked
    assert isinstance(result, dict)
    assert result["age"] == DATA_MASKING_STRING
    assert result["name"] == "powertools"


# ---------------------------
# Test with a custom class that implements dict()
# ---------------------------
class MyCustomClass:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def dict(self):
        return {"name": self.name, "age": self.age}

def test_erase_on_custom_class(data_masker):
    # GIVEN an instance of a custom class with a dict() method
    custom_instance = MyCustomClass("powertools", 5)
    
    # WHEN calling erase with fields=["age"]
    result = data_masker.erase(custom_instance, fields=["age"])
    
    # THEN the result should be a dict with the "age" field masked
    assert isinstance(result, dict)
    assert result["age"] == DATA_MASKING_STRING
    assert result["name"] == "powertools"