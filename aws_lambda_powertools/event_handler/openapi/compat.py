# mypy: ignore-errors
# flake8: noqa
from copy import copy

# MAINTENANCE: remove when deprecating Pydantic v1. Mypy doesn't handle two different code paths that import different
# versions of a module, so we need to ignore errors here.

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Set, Tuple, Type, Union

from typing_extensions import Annotated, Literal

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from aws_lambda_powertools.event_handler.openapi.types import (
    COMPONENT_REF_PREFIX,
    PYDANTIC_V2,
    ModelNameMap,
)

if PYDANTIC_V2:
    from pydantic import TypeAdapter
    from pydantic._internal._typing_extra import eval_type_lenient
    from pydantic.fields import FieldInfo
    from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
    from pydantic_core import PydanticUndefined, PydanticUndefinedType

    from aws_lambda_powertools.event_handler.openapi.types import IncEx

    Undefined = PydanticUndefined
    Required = PydanticUndefined
    UndefinedType = PydanticUndefinedType

    evaluate_forwardref = eval_type_lenient

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

else:
    from pydantic import BaseModel
    from pydantic.fields import ModelField, Required, Undefined, UndefinedType
    from pydantic.schema import (
        field_schema,
        get_annotation_from_field_info,
        get_flat_models_from_fields,
        get_model_name_map,
        model_process_schema,
    )
    from pydantic.typing import evaluate_forwardref

    JsonSchemaValue = Dict[str, Any]

    @dataclass
    class GenerateJsonSchema:
        ref_template: str

    def get_schema_from_model_field(
        *,
        field: ModelField,
        model_name_map: ModelNameMap,
        field_mapping: Dict[
            Tuple[ModelField, Literal["validation", "serialization"]],
            JsonSchemaValue,
        ],
    ) -> Dict[str, Any]:
        return field_schema(
            field,
            model_name_map=model_name_map,
            ref_prefix=COMPONENT_REF_PREFIX,
        )[0]

    def get_definitions(
        *,
        fields: List[ModelField],
        schema_generator: GenerateJsonSchema,
        model_name_map: ModelNameMap,
    ) -> Tuple[
        Dict[Tuple[ModelField, Literal["validation", "serialization"]], JsonSchemaValue],
        Dict[str, Dict[str, Any]],
    ]:
        models = get_flat_models_from_fields(fields, known_models=set())
        return {}, get_model_definitions(flat_models=models, model_name_map=model_name_map)

    def get_model_definitions(
        *,
        flat_models: Set[Union[Type[BaseModel], Type[Enum]]],
        model_name_map: ModelNameMap,
    ) -> Dict[str, Any]:
        definitions: Dict[str, Dict[str, Any]] = {}
        for model in flat_models:
            m_schema, m_definitions, _ = model_process_schema(
                model,
                model_name_map=model_name_map,
                ref_prefix=COMPONENT_REF_PREFIX,
            )
            definitions.update(m_definitions)
            model_name = model_name_map[model]
            if "description" in m_schema:
                m_schema["description"] = m_schema["description"].split("\f")[0]
            definitions[model_name] = m_schema
        return definitions

    def get_compat_model_name_map(fields: List[ModelField]) -> ModelNameMap:
        models = get_flat_models_from_fields(fields, known_models=set())
        return get_model_name_map(models)

    def model_rebuild(model: Type[BaseModel]) -> None:
        model.update_forward_refs()

    def copy_field_info(*, field_info: FieldInfo, annotation: Any) -> FieldInfo:
        return copy(field_info)
