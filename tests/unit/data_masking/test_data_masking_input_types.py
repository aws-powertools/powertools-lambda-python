import dataclasses
import pytest
from pydantic import BaseModel

from aws_lambda_powertools.utilities.data_masking.base import DataMasking, prepare_data
from aws_lambda_powertools.utilities.data_masking.constants import DATA_MASKING_STRING

@pytest.fixture
def data_masker() -> DataMasking:
    return DataMasking()


# ---------------------------
# Direct tests for prepare_data()
# ---------------------------
def test_prepare_data_primitive():
    # Primitives should be returned unchanged.
    assert prepare_data("hello") == "hello"
    assert prepare_data(123) == 123
    assert prepare_data(3.14) == 3.14
    assert prepare_data(True) is True
    assert prepare_data(None) is None


def test_prepare_data_dict_no_change():
    # A plain dict should remain unchanged.
    data = {"x": "y", "z": 10}
    result = prepare_data(data)
    assert isinstance(result, dict)
    assert result == data


def test_prepare_data_list():
    # Lists should be processed element by element.
    data = [1, "a", {"b": 2}]
    result = prepare_data(data)
    assert isinstance(result, list)
    assert result == [1, "a", {"b": 2}]


def test_prepare_data_tuple():
    # Tuples should be processed and returned as tuples.
    data = (1, 2, {"a": 3})
    result = prepare_data(data)
    assert isinstance(result, tuple)
    assert result[2]["a"] == 3


def test_prepare_data_set():
    # Sets should be processed and returned as sets.
    data = {1, 2, 3}
    result = prepare_data(data)
    assert isinstance(result, set)
    assert result == {1, 2, 3}


def test_prepare_data_dataclass():
    # Dataclasses should be converted using dataclasses.asdict.
    @dataclasses.dataclass
    class MyDataClass:
        name: str
        age: int

    instance = MyDataClass(name="delta", age=50)
    result = prepare_data(instance)
    assert isinstance(result, dict)
    assert result["name"] == "delta"
    assert result["age"] == 50


def test_prepare_data_pydantic():
    # Pydantic models should be converted using model_dump.
    class MyPydanticModel(BaseModel):
        name: str
        age: int

    instance = MyPydanticModel(name="alpha", age=30)
    result = prepare_data(instance)
    assert isinstance(result, dict)
    assert result["name"] == "alpha"
    assert result["age"] == 30


def test_prepare_data_custom_class_with_dict():
    # Custom classes that implement dict() should be processed.
    class MyCustom:
        def __init__(self, name, age):
            self.name = name
            self.age = age

        def dict(self):
            return {"name": self.name, "age": self.age}

    instance = MyCustom("beta", 40)
    result = prepare_data(instance)
    assert isinstance(result, dict)
    assert result["name"] == "beta"
    assert result["age"] == 40


def test_prepare_data_fallback_dict_via_dunder():
    # Objects with __dict__ should be converted via vars().
    class WithDict:
        def __init__(self, value):
            self.value = value

    instance = WithDict(100)
    result = prepare_data(instance)
    assert isinstance(result, dict)
    assert result["value"] == 100


def test_prepare_data_nested_structure():
    # Test a nested structure mixing dataclass, Pydantic model, custom class, and dict.
    @dataclasses.dataclass
    class NestedDC:
        x: int
        y: str

    class NestedPM(BaseModel):
        a: int
        b: str

    class NestedCustom:
        def __init__(self, z):
            self.z = z
        def dict(self):
            return {"z": self.z}

    data = {
        "dc": NestedDC(x=10, y="foo"),
        "pm": NestedPM(a=5, b="bar"),
        "custom": NestedCustom(z="baz"),
        "nested": {
            "list": [NestedDC(x=1, y="inner"), NestedPM(a=2, b="inner2")]
        }
    }
    result = prepare_data(data)
    # Assert conversions occurred.
    assert isinstance(result, dict)
    assert isinstance(result["dc"], dict)
    assert result["dc"]["x"] == 10
    assert result["dc"]["y"] == "foo"
    assert isinstance(result["pm"], dict)
    assert result["pm"]["a"] == 5
    assert result["pm"]["b"] == "bar"
    assert isinstance(result["custom"], dict)
    assert result["custom"]["z"] == "baz"
    assert isinstance(result["nested"], dict)
    assert isinstance(result["nested"]["list"], list)
    assert result["nested"]["list"][0]["y"] == "inner"
    assert result["nested"]["list"][1]["a"] == 2


def test_prepare_data_circular_reference():
    # Create a circular reference.
    data = {"a": 1}
    data["self"] = data
    result = prepare_data(data)
    assert result["a"] == 1
    assert "self" in result


# ---------------------------
# Integration tests through DataMasking.erase()
# ---------------------------
class MyPydanticModel(BaseModel):
    name: str
    age: int

@dataclasses.dataclass
class MyDataClass:
    name: str
    age: int

class MyCustomClass:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def dict(self):
        return {"name": self.name, "age": self.age}

def test_erase_on_pydantic_model(data_masker):
    # GIVEN a Pydantic model instance.
    instance = MyPydanticModel(name="powertools", age=5)
    # WHEN calling erase with fields ["age"].
    result = data_masker.erase(instance, fields=["age"])
    # THEN the "age" field is masked.
    assert isinstance(result, dict)
    assert result["age"] == DATA_MASKING_STRING
    assert result["name"] == "powertools"

def test_erase_on_dataclass(data_masker):
    # GIVEN a dataclass instance.
    instance = MyDataClass(name="powertools", age=5)
    result = data_masker.erase(instance, fields=["age"])
    assert isinstance(result, dict)
    assert result["age"] == DATA_MASKING_STRING
    assert result["name"] == "powertools"

def test_erase_on_custom_class(data_masker):
    # GIVEN a custom class instance with dict() method.
    instance = MyCustomClass("powertools", 5)
    result = data_masker.erase(instance, fields=["age"])
    assert isinstance(result, dict)
    assert result["age"] == DATA_MASKING_STRING
    assert result["name"] == "powertools"

def test_erase_on_nested_complex_structure(data_masker):
    # GIVEN a nested structure combining multiple types.
    @dataclasses.dataclass
    class NestedDC:
        value: int

    class NestedPM(BaseModel):
        value: int

    class MyCustomClass:
        def __init__(self, name, age):
            self.name = name
            self.age = age

        def dict(self):
            return {"name": self.name, "age": self.age}

    data = {
        "pydantic": NestedPM(value=10),
        "dataclass": NestedDC(value=20),
        "custom": MyCustomClass("example", 30),
        "plain_dict": {"value": 40},
        "list": [NestedPM(value=50), {"value": 60}],
    }
    # Use a recursive JSONPath expression to search for any key "value" at any depth.
    result = data_masker.erase(data, fields=["$..value"])
    
    # Verify that in each nested dict where a "value" key exists the value is masked.
    assert result["pydantic"]["value"] == DATA_MASKING_STRING
    assert result["dataclass"]["value"] == DATA_MASKING_STRING
    # "custom" branch remains unchanged because it doesn't contain a "value" key.
    assert result["custom"] == {"name": "example", "age": 30}
    assert result["plain_dict"]["value"] == DATA_MASKING_STRING
    # List items that are dicts with "value" get masked.
    assert result["list"][0]["value"] == DATA_MASKING_STRING
    assert result["list"][1]["value"] == DATA_MASKING_STRING