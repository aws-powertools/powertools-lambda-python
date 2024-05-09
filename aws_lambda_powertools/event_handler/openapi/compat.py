# mypy: ignore-errors
# flake8: noqa
from collections import deque
from copy import copy

# MAINTENANCE: remove when deprecating Pydantic v1. Mypy doesn't handle two different code paths that import different
# versions of a module, so we need to ignore errors here.

from dataclasses import dataclass, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Set, Tuple, Type, Union, FrozenSet, Deque, Sequence, Mapping

from typing_extensions import Annotated, Literal, get_origin, get_args

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo

from aws_lambda_powertools.event_handler.openapi.types import (
    COMPONENT_REF_PREFIX,
    ModelNameMap,
    UnionType,
)

from pydantic import TypeAdapter, ValidationError
from pydantic._internal._typing_extra import eval_type_lenient
from pydantic.fields import FieldInfo
from pydantic._internal._utils import lenient_issubclass
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import PydanticUndefined, PydanticUndefinedType

from aws_lambda_powertools.event_handler.openapi.types import IncEx

Undefined = PydanticUndefined
Required = PydanticUndefined
UndefinedType = PydanticUndefinedType

evaluate_forwardref = eval_type_lenient

sequence_annotation_to_type = {
    Sequence: list,
    List: list,
    list: list,
    Tuple: tuple,
    tuple: tuple,
    Set: set,
    set: set,
    FrozenSet: frozenset,
    frozenset: frozenset,
    Deque: deque,
    deque: deque,
}

sequence_types = tuple(sequence_annotation_to_type.keys())

RequestErrorModel: Type[BaseModel] = create_model("Request")


class ErrorWrapper(Exception):
    pass


@dataclass
class ModelField:
    field_info: FieldInfo
    name: str
    mode: Literal["validation", "serialization"] = "validation"

    @property
    def alias(self) -> str:
        value = self.field_info.alias
        return value if value is not None else self.name

    @property
    def required(self) -> bool:
        return self.field_info.is_required()

    @property
    def default(self) -> Any:
        return self.get_default()

    @property
    def type_(self) -> Any:
        return self.field_info.annotation

    def __post_init__(self) -> None:
        self._type_adapter: TypeAdapter[Any] = TypeAdapter(
            Annotated[self.field_info.annotation, self.field_info],
        )

    def get_default(self) -> Any:
        if self.field_info.is_required():
            return Undefined
        return self.field_info.get_default(call_default_factory=True)

    def serialize(
        self,
        value: Any,
        *,
        mode: Literal["json", "python"] = "json",
        include: Union[IncEx, None] = None,
        exclude: Union[IncEx, None] = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Any:
        return self._type_adapter.dump_python(
            value,
            mode=mode,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def validate(
        self, value: Any, values: Dict[str, Any] = {}, *, loc: Tuple[Union[int, str], ...] = ()
    ) -> Tuple[Any, Union[List[Dict[str, Any]], None]]:
        try:
            return (self._type_adapter.validate_python(value, from_attributes=True), None)
        except ValidationError as exc:
            return None, _regenerate_error_with_loc(errors=exc.errors(), loc_prefix=loc)

    def __hash__(self) -> int:
        # Each ModelField is unique for our purposes
        return id(self)


def get_schema_from_model_field(
    *,
    field: ModelField,
    model_name_map: ModelNameMap,
    field_mapping: Dict[
        Tuple[ModelField, Literal["validation", "serialization"]],
        JsonSchemaValue,
    ],
) -> Dict[str, Any]:
    json_schema = field_mapping[(field, field.mode)]
    if "$ref" not in json_schema:
        # MAINTENANCE: remove when deprecating Pydantic v1
        # Ref: https://github.com/pydantic/pydantic/blob/d61792cc42c80b13b23e3ffa74bc37ec7c77f7d1/pydantic/schema.py#L207
        json_schema["title"] = field.field_info.title or field.alias.title().replace("_", " ")
    return json_schema


def get_definitions(
    *,
    fields: List[ModelField],
    schema_generator: GenerateJsonSchema,
    model_name_map: ModelNameMap,
) -> Tuple[
    Dict[
        Tuple[ModelField, Literal["validation", "serialization"]],
        Dict[str, Any],
    ],
    Dict[str, Dict[str, Any]],
]:
    inputs = [(field, field.mode, field._type_adapter.core_schema) for field in fields]
    field_mapping, definitions = schema_generator.generate_definitions(inputs=inputs)

    return field_mapping, definitions


def get_compat_model_name_map(fields: List[ModelField]) -> ModelNameMap:
    return {}


def get_annotation_from_field_info(annotation: Any, field_info: FieldInfo, field_name: str) -> Any:
    return annotation


def model_rebuild(model: Type[BaseModel]) -> None:
    model.model_rebuild()


def copy_field_info(*, field_info: FieldInfo, annotation: Any) -> FieldInfo:
    return type(field_info).from_annotation(annotation)


def get_missing_field_error(loc: Tuple[str, ...]) -> Dict[str, Any]:
    error = ValidationError.from_exception_data(
        "Field required", [{"type": "missing", "loc": loc, "input": {}}]
    ).errors()[0]
    error["input"] = None
    return error


def is_scalar_field(field: ModelField) -> bool:
    from aws_lambda_powertools.event_handler.openapi.params import Body

    return field_annotation_is_scalar(field.field_info.annotation) and not isinstance(field.field_info, Body)


def is_scalar_sequence_field(field: ModelField) -> bool:
    return field_annotation_is_scalar_sequence(field.field_info.annotation)


def is_sequence_field(field: ModelField) -> bool:
    return field_annotation_is_sequence(field.field_info.annotation)


def is_bytes_field(field: ModelField) -> bool:
    return is_bytes_or_nonable_bytes_annotation(field.type_)


def is_bytes_sequence_field(field: ModelField) -> bool:
    return is_bytes_sequence_annotation(field.type_)


def serialize_sequence_value(*, field: ModelField, value: Any) -> Sequence[Any]:
    origin_type = get_origin(field.field_info.annotation) or field.field_info.annotation
    if not issubclass(origin_type, sequence_types):  # type: ignore[arg-type]
        raise AssertionError(f"Expected sequence type, got {origin_type}")
    return sequence_annotation_to_type[origin_type](value)  # type: ignore[no-any-return]


def _normalize_errors(errors: Sequence[Any]) -> List[Dict[str, Any]]:
    return errors  # type: ignore[return-value]


def create_body_model(*, fields: Sequence[ModelField], model_name: str) -> Type[BaseModel]:
    field_params = {f.name: (f.field_info.annotation, f.field_info) for f in fields}
    model: Type[BaseModel] = create_model(model_name, **field_params)
    return model


def _model_dump(model: BaseModel, mode: Literal["json", "python"] = "json", **kwargs: Any) -> Any:
    return model.model_dump(mode=mode, **kwargs)


def model_json(model: BaseModel, **kwargs: Any) -> Any:
    return model.model_dump_json(**kwargs)


# Common code for both versions


def field_annotation_is_complex(annotation: Union[Type[Any], None]) -> bool:
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        return any(field_annotation_is_complex(arg) for arg in get_args(annotation))

    return (
        _annotation_is_complex(annotation)
        or _annotation_is_complex(origin)
        or hasattr(origin, "__pydantic_core_schema__")
        or hasattr(origin, "__get_pydantic_core_schema__")
    )


def field_annotation_is_scalar(annotation: Any) -> bool:
    return annotation is Ellipsis or not field_annotation_is_complex(annotation)


def field_annotation_is_sequence(annotation: Union[Type[Any], None]) -> bool:
    return _annotation_is_sequence(annotation) or _annotation_is_sequence(get_origin(annotation))


def field_annotation_is_scalar_sequence(annotation: Union[Type[Any], None]) -> bool:
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        at_least_one_scalar_sequence = False
        for arg in get_args(annotation):
            if field_annotation_is_scalar_sequence(arg):
                at_least_one_scalar_sequence = True
                continue
            elif not field_annotation_is_scalar(arg):
                return False
        return at_least_one_scalar_sequence
    return field_annotation_is_sequence(annotation) and all(
        field_annotation_is_scalar(sub_annotation) for sub_annotation in get_args(annotation)
    )


def is_bytes_or_nonable_bytes_annotation(annotation: Any) -> bool:
    if lenient_issubclass(annotation, bytes):
        return True
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        for arg in get_args(annotation):
            if lenient_issubclass(arg, bytes):
                return True
    return False


def is_bytes_sequence_annotation(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        at_least_one = False
        for arg in get_args(annotation):
            if is_bytes_sequence_annotation(arg):
                at_least_one = True
                break
        return at_least_one
    return field_annotation_is_sequence(annotation) and all(
        is_bytes_or_nonable_bytes_annotation(sub_annotation) for sub_annotation in get_args(annotation)
    )


def value_is_sequence(value: Any) -> bool:
    return isinstance(value, sequence_types) and not isinstance(value, (str, bytes))  # type: ignore[arg-type]


def _annotation_is_complex(annotation: Union[Type[Any], None]) -> bool:
    return (
        lenient_issubclass(annotation, (BaseModel, Mapping))  # TODO: UploadFile
        or _annotation_is_sequence(annotation)
        or is_dataclass(annotation)
    )


def _annotation_is_sequence(annotation: Union[Type[Any], None]) -> bool:
    if lenient_issubclass(annotation, (str, bytes)):
        return False
    return lenient_issubclass(annotation, sequence_types)


def _regenerate_error_with_loc(
    *, errors: Sequence[Any], loc_prefix: Tuple[Union[str, int], ...]
) -> List[Dict[str, Any]]:
    updated_loc_errors: List[Any] = [
        {**err, "loc": loc_prefix + err.get("loc", ())} for err in _normalize_errors(errors)
    ]

    return updated_loc_errors
