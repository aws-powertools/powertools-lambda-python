from __future__ import annotations

import datetime as dt
from dataclasses import fields, is_dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints
from uuid import UUID

from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyModelTypeError,
    IdempotencyNoSerializationModelError,
)
from aws_lambda_powertools.utilities.idempotency.serialization.base import (
    BaseIdempotencyModelSerializer,
    BaseIdempotencySerializer,
)
from aws_lambda_powertools.utilities.idempotency.serialization.functions import get_actual_type

DataClass = Any


def _to_json_compatible(value: Any) -> Any:
    """Convert a dataclass result into values the idempotency JSON encoder can store."""
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _to_json_compatible(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return _to_json_compatible(value.value)
    if isinstance(value, dict):
        return {k: _to_json_compatible(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_to_json_compatible(v) for v in value]
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    return str(value) if isinstance(value, UUID) else value


def _convert_union(value: Any, type_hint: Any) -> Any:
    for arg in get_args(type_hint):
        if arg is type(None):
            continue
        converted = _from_json_compatible(value, arg)
        if converted is not value:
            return converted
    return value


def _convert_sequence(value: list, origin: type, type_hint: Any) -> Any:
    args = get_args(type_hint)
    if origin is tuple and args and not (len(args) == 2 and args[1] is Ellipsis):
        items = [_from_json_compatible(v, a) for v, a in zip(value, args, strict=False)]
        items.extend(value[len(items) :])
    else:
        item_type = args[0] if args else Any
        items = [_from_json_compatible(v, item_type) for v in value]
    return items if origin is list else origin(items)


def _convert_scalar(value: Any, type_hint: type) -> Any:
    if issubclass(type_hint, Enum):
        return type_hint(value)
    if not isinstance(value, str):
        return value
    if issubclass(type_hint, (dt.datetime, dt.date, dt.time)):
        return type_hint.fromisoformat(value)
    if issubclass(type_hint, (UUID, Decimal)):
        return type_hint(value)
    return value


def _from_json_compatible(value: Any, type_hint: Any) -> Any:
    """Rebuild a stored value into the type declared on the dataclass field.

    Values that don't match the declared type are returned untouched, so records
    stored before this conversion existed keep being replayed as they were.
    """
    origin = get_origin(type_hint)
    result = value

    if value is None:
        result = None
    elif origin is Union or origin is UnionType:
        result = _convert_union(value, type_hint)
    elif origin in (list, set, frozenset, tuple) and isinstance(value, list):
        result = _convert_sequence(value, origin, type_hint)
    elif origin is dict and isinstance(value, dict):
        args = get_args(type_hint)
        value_type = args[1] if len(args) == 2 else Any
        result = {k: _from_json_compatible(v, value_type) for k, v in value.items()}
    elif isinstance(type_hint, type) and is_dataclass(type_hint) and isinstance(value, dict):
        result = _build_dataclass(type_hint, value)
    elif isinstance(type_hint, type):
        try:
            result = _convert_scalar(value, type_hint)
        except (ValueError, TypeError, InvalidOperation):
            result = value

    return result


def _build_dataclass(model: type[DataClass], data: dict) -> DataClass:
    try:
        hints = get_type_hints(model)
    except Exception:  # unresolvable forward references: fall back to the raw annotations
        hints = {}

    converted = {}
    for key, value in data.items():
        type_hint = hints.get(key)
        converted[key] = _from_json_compatible(value, type_hint) if type_hint is not None else value
    return model(**converted)


class DataclassSerializer(BaseIdempotencyModelSerializer):
    """
    A serializer class for transforming data between dataclass objects and dictionaries.
    """

    def __init__(self, model: type[DataClass]):
        """
        Parameters
        ----------
        model: type[DataClass]
            A dataclass type to be used for serialization and deserialization
        """
        self.__model: type[DataClass] = model

    def to_dict(self, data: DataClass) -> dict:
        # The result is stored as JSON, so dump JSON-compatible values; from_dict rebuilds them from the field types.
        return _to_json_compatible(data)

    def from_dict(self, data: dict) -> DataClass:
        return _build_dataclass(self.__model, data)

    @classmethod
    def instantiate(cls, model_type: Any) -> BaseIdempotencySerializer:
        model_type = get_actual_type(model_type=model_type)

        if model_type is None:
            raise IdempotencyNoSerializationModelError("No serialization model was supplied")

        if not is_dataclass(model_type):
            raise IdempotencyModelTypeError("Model type is not inherited of dataclass type")
        return cls(model=model_type)  # type: ignore[arg-type]
