import inspect
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseConfig
from pydantic.fields import FieldInfo
from typing_extensions import Annotated, Literal, get_args, get_origin

from aws_lambda_powertools.event_handler.openapi.compat import (
    ModelField,
    Required,
    Undefined,
    UndefinedType,
    copy_field_info,
    field_annotation_is_scalar,
    get_annotation_from_field_info,
)
from aws_lambda_powertools.event_handler.openapi.types import PYDANTIC_V2, CacheKey

"""
This turns the low-level function signature into typed, validated Pydantic models for consumption.
"""


class ParamTypes(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


# MAINTENANCE: update when deprecating Pydantic v1, remove this alias
_Unset: Any = Undefined


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
        self.cache_key: CacheKey = self.call


class Param(FieldInfo):
    """
    A class used internally to represent a parameter in a path operation.
    """

    in_: ParamTypes

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # MAINTENANCE: update when deprecating Pydantic v1, import these types
        # MAINTENANCE: validation_alias: str | AliasPath | AliasChoices | None
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
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        self.deprecated = deprecated
        self.include_in_schema = include_in_schema

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
        if PYDANTIC_V2:
            kwargs.update(
                {
                    "annotation": annotation,
                    "alias_priority": alias_priority,
                    "validation_alias": validation_alias,
                    "serialization_alias": serialization_alias,
                    "strict": strict,
                    "json_schema_extra": current_json_schema_extra,
                },
            )
            kwargs["pattern"] = pattern
        else:
            kwargs["regex"] = pattern
            kwargs.update(**current_json_schema_extra)

        use_kwargs = {k: v for k, v in kwargs.items() if v is not _Unset}

        super().__init__(**use_kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Path(Param):
    """
    A class used internally to represent a path parameter in a path operation.
    """

    in_ = ParamTypes.path

    def __init__(
        self,
        default: Any = ...,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # MAINTENANCE: update when deprecating Pydantic v1, import these types
        # MAINTENANCE: validation_alias: str | AliasPath | AliasChoices | None
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
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        if default is not ...:
            raise AssertionError("Path parameters cannot have a default value")

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
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Query(Param):
    """
    A class used internally to represent a query parameter in a path operation.
    """

    in_ = ParamTypes.query

    def __init__(
        self,
        default: Any = _Unset,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
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
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
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
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Header(Param):
    """
    A class used internally to represent a header parameter in a path operation.
    """

    in_ = ParamTypes.header

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # MAINTENANCE: update when deprecating Pydantic v1, import these types
        # str | AliasPath | AliasChoices | None
        validation_alias: Union[str, None] = None,
        serialization_alias: Union[str, None] = None,
        convert_underscores: bool = True,
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
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        self.convert_underscores = convert_underscores
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
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class Body(FieldInfo):
    """
    A class used internally to represent a body parameter in a path operation.
    """

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        embed: bool = False,
        media_type: str = "application/json",
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # MAINTENANCE: update when deprecating Pydantic v1, import these types
        # str | AliasPath | AliasChoices | None
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
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        self.embed = embed
        self.media_type = media_type
        self.deprecated = deprecated
        self.include_in_schema = include_in_schema
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
        if PYDANTIC_V2:
            kwargs.update(
                {
                    "annotation": annotation,
                    "alias_priority": alias_priority,
                    "validation_alias": validation_alias,
                    "serialization_alias": serialization_alias,
                    "strict": strict,
                    "json_schema_extra": current_json_schema_extra,
                },
            )
            kwargs["pattern"] = pattern
        else:
            kwargs["regex"] = pattern
            kwargs.update(**current_json_schema_extra)

        use_kwargs = {k: v for k, v in kwargs.items() if v is not _Unset}

        super().__init__(**use_kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.default})"


class Form(Body):
    """
    A class used internally to represent a form parameter in a path operation.
    """

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        media_type: str = "application/x-www-form-urlencoded",
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # MAINTENANCE: update when deprecating Pydantic v1, import these types
        # str | AliasPath | AliasChoices | None
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
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            embed=True,
            media_type=media_type,
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
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


class File(Form):
    """
    A class used internally to represent a file parameter in a path operation.
    """

    def __init__(
        self,
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        annotation: Optional[Any] = None,
        media_type: str = "multipart/form-data",
        alias: Optional[str] = None,
        alias_priority: Union[int, None] = _Unset,
        # MAINTENANCE: update when deprecating Pydantic v1, import these types
        # str | AliasPath | AliasChoices | None
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
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: Union[Dict[str, Any], None] = None,
        **extra: Any,
    ):
        super().__init__(
            default=default,
            default_factory=default_factory,
            annotation=annotation,
            media_type=media_type,
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
            include_in_schema=include_in_schema,
            json_schema_extra=json_schema_extra,
            **extra,
        )


def get_flat_dependant(
    dependant: Dependant,
    *,
    skip_repeats: bool = False,
    visited: Optional[List[CacheKey]] = None,
) -> Dependant:
    """
    Flatten a recursive Dependant model structure.

    This function recursively concatenates the parameter fields of a Dependant model and its dependencies into a flat
    Dependant structure. This is useful for scenarios like parameter validation where the nested structure is not
    relevant.

    Parameters
    ----------
    dependant: Dependant
        The dependant model to flatten
    skip_repeats: bool
        If True, child Dependents already visited will be skipped to avoid duplicates
    visited: List[CacheKey], optional
        Keeps track of visited Dependents to avoid infinite recursion. Defaults to empty list.

    Returns
    -------
    Dependant
        The flattened Dependant model
    """
    if visited is None:
        visited = []
    visited.append(dependant.cache_key)

    flat_dependant = Dependant(
        path_params=dependant.path_params.copy(),
        query_params=dependant.query_params.copy(),
        header_params=dependant.header_params.copy(),
        cookie_params=dependant.cookie_params.copy(),
        body_params=dependant.body_params.copy(),
        path=dependant.path,
    )
    for sub_dependant in dependant.dependencies:
        if skip_repeats and sub_dependant.cache_key in visited:
            continue

        flat_sub = get_flat_dependant(sub_dependant, skip_repeats=skip_repeats, visited=visited)

        flat_dependant.path_params.extend(flat_sub.path_params)
        flat_dependant.query_params.extend(flat_sub.query_params)
        flat_dependant.header_params.extend(flat_sub.header_params)
        flat_dependant.cookie_params.extend(flat_sub.cookie_params)
        flat_dependant.body_params.extend(flat_sub.body_params)

    return flat_dependant


def analyze_param(
    *,
    param_name: str,
    annotation: Any,
    value: Any,
    is_path_param: bool,
    is_response_param: bool,
) -> Optional[ModelField]:
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
    is_response_param
        Whether the parameter is the return annotation

    Returns
    -------
    Optional[ModelField]
        The type annotation and the Pydantic field representing the parameter
    """
    field_info, type_annotation = _get_field_info_and_type_annotation(annotation, value, is_path_param)

    # If the value is a FieldInfo, we use it as the FieldInfo for the parameter
    if isinstance(value, FieldInfo):
        if field_info is not None:
            raise AssertionError("Cannot use a FieldInfo as a parameter annotation and pass a FieldInfo as a value")
        field_info = value

        if PYDANTIC_V2:
            field_info.annotation = type_annotation  # type: ignore[attr-defined,unused-ignore]

    # If we didn't determine the FieldInfo yet, we create a default one
    if field_info is None:
        default_value = value if value is not inspect.Signature.empty else Required

        # Check if the parameter is part of the path. Otherwise, defaults to query.
        if is_path_param:
            field_info = Path(annotation=type_annotation)
        elif not field_annotation_is_scalar(annotation=type_annotation):
            field_info = Body(annotation=type_annotation, default=default_value)
        else:
            field_info = Query(annotation=type_annotation, default=default_value)

    # When we have a response field, we need to set the default value to Required
    if is_response_param:
        field_info.default = Required

    field = _create_model_field(field_info, type_annotation, param_name, is_path_param)
    return field


def _get_field_info_and_type_annotation(annotation, value, is_path_param: bool) -> Tuple[Optional[FieldInfo], Any]:
    """
    Get the FieldInfo and type annotation from an annotation and value.
    """
    field_info: Optional[FieldInfo] = None
    type_annotation: Any = Any

    if annotation is not inspect.Signature.empty:
        # If the annotation is an Annotated type, we need to extract the type annotation and the FieldInfo
        if get_origin(annotation) is Annotated:
            field_info, type_annotation = _get_field_info_annotated_type(annotation, value, is_path_param)
        # If the annotation is not an Annotated type, we use it as the type annotation
        else:
            type_annotation = annotation

    return field_info, type_annotation


def _get_field_info_annotated_type(annotation, value, is_path_param: bool) -> Tuple[Optional[FieldInfo], Any]:
    """
    Get the FieldInfo and type annotation from an Annotated type.
    """
    field_info: Optional[FieldInfo] = None
    annotated_args = get_args(annotation)
    type_annotation = annotated_args[0]
    powertools_annotations = [arg for arg in annotated_args[1:] if isinstance(arg, FieldInfo)]

    if len(powertools_annotations) > 1:
        raise AssertionError("Only one FieldInfo can be used per parameter")

    powertools_annotation = next(iter(powertools_annotations), None)

    if isinstance(powertools_annotation, FieldInfo):
        # Copy `field_info` because we mutate `field_info.default` later
        field_info = copy_field_info(
            field_info=powertools_annotation,
            annotation=annotation,
        )
        if field_info.default not in [Undefined, Required]:
            raise AssertionError("FieldInfo needs to have a default value of Undefined or Required")

        if value is not inspect.Signature.empty:
            if is_path_param:
                raise AssertionError("Cannot use a FieldInfo as a path parameter and pass a value")
            field_info.default = value
        else:
            field_info.default = Required

    return field_info, type_annotation


def _create_response_field(
    name: str,
    type_: Type[Any],
    default: Optional[Any] = Undefined,
    required: Union[bool, UndefinedType] = Undefined,
    model_config: Type[BaseConfig] = BaseConfig,
    field_info: Optional[FieldInfo] = None,
    alias: Optional[str] = None,
    mode: Literal["validation", "serialization"] = "validation",
) -> ModelField:
    """
    Create a new response field. Raises if type_ is invalid.
    """
    if PYDANTIC_V2:
        field_info = field_info or FieldInfo(
            annotation=type_,
            default=default,
            alias=alias,
        )
    else:
        field_info = field_info or FieldInfo()
    kwargs = {"name": name, "field_info": field_info}
    if PYDANTIC_V2:
        kwargs.update({"mode": mode})
    else:
        kwargs.update(
            {
                "type_": type_,
                "class_validators": {},
                "default": default,
                "required": required,
                "model_config": model_config,
                "alias": alias,
            },
        )
    return ModelField(**kwargs)  # type: ignore[arg-type]


def _create_model_field(
    field_info: Optional[FieldInfo],
    type_annotation: Any,
    param_name: str,
    is_path_param: bool,
) -> Optional[ModelField]:
    """
    Create a new ModelField from a FieldInfo and type annotation.
    """
    if field_info is None:
        return None

    if is_path_param:
        if not isinstance(field_info, Path):
            raise AssertionError("Path parameters must be of type Path")
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

    return _create_response_field(
        name=param_name,
        type_=use_annotation,
        default=field_info.default,
        alias=alias,
        required=field_info.default in (Required, Undefined),
        field_info=field_info,
    )
