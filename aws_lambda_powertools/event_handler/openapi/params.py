import inspect
from copy import copy
from enum import Enum
from typing import Annotated, Any, Callable, Dict, List, Optional, Tuple, Union, get_args, get_origin

from pydantic import BaseConfig
from pydantic.fields import FieldInfo, ModelField, Required, Undefined
from pydantic.schema import get_annotation_from_field_info

from aws_lambda_powertools.event_handler.openapi import Example

"""
This turns the low-level function signature into typed, validated Pydantic models for consumption.
"""


class Dependant:
    """
    A class used internally to represent a dependency between path operation decorators and the path operation function.
    """

    def __init__(
        self,
        *,
        path_params: Optional[List[ModelField]] = None,
        query_params: Optional[List[ModelField]] = None,
        header_params: Optional[List[ModelField]] = None,
        cookie_params: Optional[List[ModelField]] = None,
        body_params: Optional[List[ModelField]] = None,
        return_param: Optional[ModelField] = None,
        dependencies: Optional[List["Dependant"]] = None,
        name: Optional[str] = None,
        call: Optional[Callable[..., Any]] = None,
        request_param_name: Optional[str] = None,
        websocket_param_name: Optional[str] = None,
        http_connection_param_name: Optional[str] = None,
        response_param_name: Optional[str] = None,
        background_tasks_param_name: Optional[str] = None,
        path: Optional[str] = None,
    ) -> None:
        self.path_params = path_params or []
        self.query_params = query_params or []
        self.header_params = header_params or []
        self.cookie_params = cookie_params or []
        self.body_params = body_params or []
        self.return_param = return_param or None
        self.dependencies = dependencies or []
        self.request_param_name = request_param_name
        self.websocket_param_name = websocket_param_name
        self.http_connection_param_name = http_connection_param_name
        self.response_param_name = response_param_name
        self.background_tasks_param_name = background_tasks_param_name
        self.name = name
        self.call = call
        # Store the path to be able to re-generate a dependable from it in overrides
        self.path = path
        # Save the cache key at creation to optimize performance
        self.cache_key = self.call


class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


class Param(FieldInfo):
    in_: ParamTypes

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = Undefined,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = Undefined,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = Undefined,
        multiple_of: Union[float, None] = Undefined,
        allow_inf_nan: Union[bool, None] = Undefined,
        max_digits: Union[int, None] = Undefined,
        decimal_places: Union[int, None] = Undefined,
        examples: Optional[List[Any]] = None,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        self.deprecated = deprecated
        self.include_in_schema = include_in_schema
        self.openapi_examples = openapi_examples
        kwargs = dict(
            default=default,
            default_factory=default_factory,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            discriminator=discriminator,
            multiple_of=multiple_of,
            allow_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            **extra,
        )
        if examples is not None:
            kwargs["examples"] = examples

        current_json_schema_extra = json_schema_extra or extra
        kwargs["regex"] = pattern
        kwargs.update(**current_json_schema_extra)
        use_kwargs = {k: v for k, v in kwargs.items() if v is not Undefined}

        super().__init__(**use_kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Path(Param):
    in_ = ParamTypes.path

    def __init__(
        self,
        default: Any = ...,
        *,
        default_factory: Union[Callable[[], Any], None] = Undefined,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = Undefined,
        # TODO: update when deprecating Pydantic v1, import these types
        # validation_alias: str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = Undefined,
        multiple_of: Union[float, None] = Undefined,
        allow_inf_nan: Union[bool, None] = Undefined,
        max_digits: Union[int, None] = Undefined,
        decimal_places: Union[int, None] = Undefined,
        examples: Optional[List[Any]] = None,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        assert default is ..., "Path parameters cannot have a default value"
        self.in_ = self.in_
        super(Path, self).__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Query(Param):
    in_ = ParamTypes.query

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = Undefined,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = Undefined,
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = Undefined,
        multiple_of: Union[float, None] = Undefined,
        allow_inf_nan: Union[bool, None] = Undefined,
        max_digits: Union[int, None] = Undefined,
        decimal_places: Union[int, None] = Undefined,
        examples: Optional[List[Any]] = None,
        openapi_examples: Optional[Dict[str, Example]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            alias=alias,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            discriminator=discriminator,
            strict=strict,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            deprecated=deprecated,
            examples=examples,
            openapi_examples=openapi_examples,
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


def analyze_param(
    *,
    param_name: str,
    annotation: Any,
    value: Any,
    is_path_param: bool,
) -> Tuple[Any, Optional[ModelField]]:
    """
    Analyze a parameter annotation and value to determine the type and default value of the parameter.

    Parameters
    ----------
    param_name: str
        The name of the parameter
    annotation
        The annotation of the parameter
    value
        The value of the parameter
    is_path_param
        Whether the parameter is a path parameter

    Returns
    -------
    Tuple[Any, Optional[ModelField]]
        The type annotation and the Pydantic field representing the parameter
    """
    field_info: Optional[FieldInfo] = None
    type_annotation: Any = Any

    # If the annotation is an Annotated type, we need to extract the type annotation and the FieldInfo
    if annotation is not inspect.Signature.empty and get_origin(annotation) is Annotated:
        annotated_args = get_args(annotation)
        type_annotation = annotated_args[0]
        powertools_annotations = [arg for arg in annotated_args[1:] if isinstance(arg, FieldInfo)]
        assert len(powertools_annotations) <= 1

        powertools_annotation = next(iter(powertools_annotations), None)

        if isinstance(powertools_annotation, FieldInfo):
            # Copy `field_info` because we mutate `field_info.default` later
            field_info = copy(powertools_annotation)
            assert field_info.default is Undefined or field_info.default is Required

            if value is not inspect.Signature.empty:
                assert not is_path_param
                field_info.default = value
            else:
                field_info.default = Required

    # If the annotation is not an Annotated type, we use it as the type annotation
    elif annotation is not inspect.Signature.empty:
        type_annotation = annotation

    # If the value is a FieldInfo, we use it as the FieldInfo for the parameter
    if isinstance(value, FieldInfo):
        assert field_info is None
        field_info = value

    # If we didn't determine the FieldInfo yet, we create a default one
    if field_info is None:
        default_value = value if value is not inspect.Signature.empty else Required

        if is_path_param:
            field_info = Path(annotation=type_annotation, default=default_value)
        else:
            field_info = Query(annotation=type_annotation, default=default_value)

    # Now that we have the FieldInfo, we can determine the type annotation
    field = None
    if field_info is not None:
        if is_path_param:
            assert isinstance(field_info, Path), "Path parameters must be of type Path"
        elif isinstance(field_info, Param) and getattr(field_info, "in_", None) is None:
            field_info.in_ = ParamTypes.query

        # If the field_info is a Param, we use the `in_` attribute to determine the type annotation
        use_annotation = get_annotation_from_field_info(type_annotation, field_info, param_name)

        # If the field doesn't have a defined alias, we use the param name
        if not field_info.alias and getattr(field_info, "convert_underscores", None):
            alias = param_name.replace("_", "-")
        else:
            alias = field_info.alias or param_name
        field_info.alias = alias

        # Create the Pydantic field
        field = ModelField(
            name=param_name,
            field_info=field_info,
            type_=use_annotation,
            class_validators={},
            default=field_info.default,
            required=field_info.default in (Required, Undefined),
            model_config=BaseConfig,
            alias=alias,
        )

    return type_annotation, field
