import dataclasses
import datetime
from collections import defaultdict, deque
from decimal import Decimal
from enum import Enum
from pathlib import Path, PurePath
from re import Pattern
from types import GeneratorType
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from uuid import UUID

from pydantic import BaseModel
from pydantic.color import Color
from pydantic.types import SecretBytes, SecretStr

from aws_lambda_powertools.event_handler.openapi.compat import _model_dump
from aws_lambda_powertools.event_handler.openapi.exceptions import SerializationError
from aws_lambda_powertools.event_handler.openapi.types import IncEx

"""
This module contains the encoders used by jsonable_encoder to convert Python objects to JSON serializable data types.
"""


def jsonable_encoder(  # noqa: PLR0911
    obj: Any,
    include: Optional[IncEx] = None,
    exclude: Optional[IncEx] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    custom_serializer: Optional[Callable[[Any], str]] = None,
) -> Any:
    """
    JSON encodes an arbitrary Python object into JSON serializable data types.

    This is a modified version of fastapi.encoders.jsonable_encoder that supports
    encoding of pydantic.BaseModel objects.

    Parameters
    ----------
    obj : Any
        The object to encode
    include : Optional[IncEx], optional
        A set or dictionary of strings that specifies which properties should be included, by default None,
        meaning everything is included
    exclude : Optional[IncEx], optional
        A set or dictionary of strings that specifies which properties should be excluded, by default None,
        meaning nothing is excluded
    by_alias : bool, optional
        Whether field aliases should be respected, by default True
    exclude_unset : bool, optional
        Whether fields that are not set should be excluded, by default False
    exclude_defaults : bool, optional
        Whether fields that are equal to their default value (as specified in the model) should be excluded,
        by default False
    exclude_none : bool, optional
        Whether fields that are equal to None should be excluded, by default False
    custom_serializer : Callable, optional
        A custom serializer to use for encoding the object, when everything else fails.

    Returns
    -------
    Any
        The JSON serializable data types
    """
    if include is not None and not isinstance(include, (set, dict)):
        include = set(include)
    if exclude is not None and not isinstance(exclude, (set, dict)):
        exclude = set(exclude)

    try:
        # Pydantic models
        if isinstance(obj, BaseModel):
            return _dump_base_model(
                obj=obj,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_none=exclude_none,
                exclude_defaults=exclude_defaults,
            )

        # Dataclasses
        if dataclasses.is_dataclass(obj):
            obj_dict = dataclasses.asdict(obj)
            return jsonable_encoder(
                obj_dict,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                custom_serializer=custom_serializer,
            )

        # Enums
        if isinstance(obj, Enum):
            return obj.value

        # Paths
        if isinstance(obj, PurePath):
            return str(obj)

        # Scalars
        if isinstance(obj, (str, int, float, type(None))):
            return obj

        # Dictionaries
        if isinstance(obj, dict):
            return _dump_dict(
                obj=obj,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_none=exclude_none,
                custom_serializer=custom_serializer,
            )

        # Sequences
        if isinstance(obj, (list, set, frozenset, GeneratorType, tuple, deque)):
            return _dump_sequence(
                obj=obj,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_none=exclude_none,
                exclude_defaults=exclude_defaults,
                exclude_unset=exclude_unset,
                custom_serializer=custom_serializer,
            )

        # Other types
        if type(obj) in ENCODERS_BY_TYPE:
            return ENCODERS_BY_TYPE[type(obj)](obj)

        for encoder, classes_tuple in encoders_by_class_tuples.items():
            if isinstance(obj, classes_tuple):
                return encoder(obj)

        # Use custom serializer if present
        if custom_serializer:
            return custom_serializer(obj)

        # Default
        return _dump_other(
            obj=obj,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            custom_serializer=custom_serializer,
        )
    except ValueError as exc:
        raise SerializationError(
            f"Unable to serialize the object {obj} as it is not a supported type. Error details: {exc}",
            "See: https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/#serializing-objects",
        ) from exc


def _dump_base_model(
    *,
    obj: Any,
    include: Optional[IncEx] = None,
    exclude: Optional[IncEx] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_none: bool = False,
    exclude_defaults: bool = False,
):
    """
    Dump a BaseModel object to a dict, using the same parameters as jsonable_encoder
    """
    obj_dict = _model_dump(
        obj,
        mode="json",
        include=include,
        exclude=exclude,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_none=exclude_none,
        exclude_defaults=exclude_defaults,
    )
    if "__root__" in obj_dict:
        obj_dict = obj_dict["__root__"]

    return jsonable_encoder(
        obj_dict,
        exclude_none=exclude_none,
        exclude_defaults=exclude_defaults,
    )


def _dump_dict(
    *,
    obj: Any,
    include: Optional[IncEx] = None,
    exclude: Optional[IncEx] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_none: bool = False,
    custom_serializer: Optional[Callable[[Any], str]] = None,
) -> Dict[str, Any]:
    """
    Dump a dict to a dict, using the same parameters as jsonable_encoder

    Parameters
    ----------
    custom_serializer : Callable, optional
        A custom serializer to use for encoding the object, when everything else fails.
    """
    encoded_dict = {}
    allowed_keys = set(obj.keys())
    if include is not None:
        allowed_keys &= set(include)
    if exclude is not None:
        allowed_keys -= set(exclude)
    for key, value in obj.items():
        if (
            (not isinstance(key, str) or not key.startswith("_sa"))
            and (value is not None or not exclude_none)
            and key in allowed_keys
        ):
            encoded_key = jsonable_encoder(
                key,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_none=exclude_none,
                custom_serializer=custom_serializer,
            )
            encoded_value = jsonable_encoder(
                value,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_none=exclude_none,
                custom_serializer=custom_serializer,
            )
            encoded_dict[encoded_key] = encoded_value
    return encoded_dict


def _dump_sequence(
    *,
    obj: Any,
    include: Optional[IncEx] = None,
    exclude: Optional[IncEx] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_none: bool = False,
    exclude_defaults: bool = False,
    custom_serializer: Optional[Callable[[Any], str]] = None,
) -> List[Any]:
    """
    Dump a sequence to a list, using the same parameters as jsonable_encoder.
    """
    encoded_list = []
    for item in obj:
        encoded_list.append(
            jsonable_encoder(
                item,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                custom_serializer=custom_serializer,
            ),
        )
    return encoded_list


def _dump_other(
    *,
    obj: Any,
    include: Optional[IncEx] = None,
    exclude: Optional[IncEx] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_none: bool = False,
    exclude_defaults: bool = False,
    custom_serializer: Optional[Callable[[Any], str]] = None,
) -> Any:
    """
    Dump an object to a hashable object, using the same parameters as jsonable_encoder
    """
    try:
        data = dict(obj)
    except Exception as e:
        errors: List[Exception] = [e]
        try:
            data = vars(obj)
        except Exception as e:
            errors.append(e)
            raise ValueError(errors) from e
    return jsonable_encoder(
        data,
        include=include,
        exclude=exclude,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        custom_serializer=custom_serializer,
    )


def iso_format(o: Union[datetime.date, datetime.time]) -> str:
    """
    ISO format for date and time
    """
    return o.isoformat()


def decimal_encoder(dec_value: Decimal) -> Union[int, float]:
    """
    Encodes a Decimal as int of there's no exponent, otherwise float

    This is useful when we use ConstrainedDecimal to represent Numeric(x,0)
    where an integer (but not int typed) is used. Encoding this as a float
    results in failed round-tripping between encode and parse.

    >>> decimal_encoder(Decimal("1.0"))
    1.0

    >>> decimal_encoder(Decimal("1"))
    1
    """
    if dec_value.as_tuple().exponent >= 0:  # type: ignore[operator]
        return int(dec_value)
    else:
        return float(dec_value)


# Encoders for types that are not JSON serializable
ENCODERS_BY_TYPE: Dict[Type[Any], Callable[[Any], Any]] = {
    bytes: lambda o: o.decode(),
    Color: str,
    datetime.date: iso_format,
    datetime.datetime: iso_format,
    datetime.time: iso_format,
    datetime.timedelta: lambda td: td.total_seconds(),
    Decimal: decimal_encoder,
    Enum: lambda o: o.value,
    frozenset: list,
    deque: list,
    GeneratorType: list,
    Path: str,
    Pattern: lambda o: o.pattern,
    SecretBytes: str,
    SecretStr: str,
    set: list,
    UUID: str,
}


# Generates a mapping of encoders to a tuple of classes that they can encode
def generate_encoders_by_class_tuples(
    type_encoder_map: Dict[Any, Callable[[Any], Any]],
) -> Dict[Callable[[Any], Any], Tuple[Any, ...]]:
    encoders: Dict[Callable[[Any], Any], Tuple[Any, ...]] = defaultdict(tuple)
    for type_, encoder in type_encoder_map.items():
        encoders[encoder] += (type_,)
    return encoders


# Mapping of encoders to a tuple of classes that they can encode
encoders_by_class_tuples = generate_encoders_by_class_tuples(ENCODERS_BY_TYPE)
