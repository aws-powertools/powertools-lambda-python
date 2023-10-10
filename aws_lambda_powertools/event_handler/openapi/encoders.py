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
from aws_lambda_powertools.event_handler.openapi.types import IncEx


def iso_format(o: Union[datetime.date, datetime.time]) -> str:
    """
    ISO format for date and time
    """
    return o.isoformat()


def decimal_encoder(dec_value: Decimal) -> Union[int, float]:
    """
    Encodes a Decimal as int of there's no exponent, otherwise float

    This is useful when we use ConstrainedDecimal to represent Numeric(x,0)
    where a integer (but not int typed) is used. Encoding this as a float
    results in failed round-tripping between encode and parse.
    Our Id type is a prime example of this.

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


def jsonable_encoder(  # noqa: C901, PLR0911, PLR0912
    obj: Any,
    include: Optional[IncEx] = None,
    exclude: Optional[IncEx] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
) -> Any:
    """
    JSON encodes an arbitrary Python object into JSON serializable data types.
    """
    if include is not None and not isinstance(include, (set, dict)):
        include = set(include)
    if exclude is not None and not isinstance(exclude, (set, dict)):
        exclude = set(exclude)

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
        )

    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, PurePath):
        return str(obj)
    if isinstance(obj, (str, int, float, type(None))):
        return obj
    if isinstance(obj, dict):
        return _dump_dict(
            obj=obj,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
        )
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple, deque)):
        return _dump_sequence(
            obj=obj,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
            exclude_unset=exclude_unset,
        )

    if type(obj) in ENCODERS_BY_TYPE:
        return ENCODERS_BY_TYPE[type(obj)](obj)

    for encoder, classes_tuple in encoders_by_class_tuples.items():
        if isinstance(obj, classes_tuple):
            return encoder(obj)

    return _dump_other(
        obj=obj,
        include=include,
        exclude=exclude,
        by_alias=by_alias,
        exclude_none=exclude_none,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
    )


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
) -> Dict[str, Any]:
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
            )
            encoded_value = jsonable_encoder(
                value,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_none=exclude_none,
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
) -> List[Any]:
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
) -> Any:
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
    )
