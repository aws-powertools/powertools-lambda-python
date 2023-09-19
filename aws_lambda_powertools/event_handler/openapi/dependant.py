import inspect
import re
from typing import Any, Callable, Dict, ForwardRef, Optional, Set, cast

from pydantic.fields import ModelField
from pydantic.typing import evaluate_forwardref

from aws_lambda_powertools.event_handler.openapi.params import Dependant, Param, ParamTypes, analyze_param


def add_param_to_fields(
    *,
    field: ModelField,
    dependant: Dependant,
) -> None:
    field_info = cast(Param, field.field_info)
    if field_info.in_ == ParamTypes.path:
        dependant.path_params.append(field)
    elif field_info.in_ == ParamTypes.query:
        dependant.query_params.append(field)
    elif field_info.in_ == ParamTypes.header:
        dependant.header_params.append(field)
    else:
        assert field_info.in_ == ParamTypes.cookie
        dependant.cookie_params.append(field)


def get_typed_annotation(annotation: Any, globalns: Dict[str, Any]) -> Any:
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = evaluate_forwardref(annotation, globalns, globalns)
    return annotation


def get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    signature = inspect.signature(call)
    globalns = getattr(call, "__global__", {})
    typed_params = [
        inspect.Parameter(
            name=param.name,
            kind=param.kind,
            default=param.default,
            annotation=get_typed_annotation(param.annotation, globalns),
        )
        for param in signature.parameters.values()
    ]

    if signature.return_annotation is not inspect.Signature.empty:
        return_param = inspect.Parameter(
            name="Return",
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=None,
            annotation=get_typed_annotation(signature.return_annotation, globalns),
        )
        return inspect.Signature(typed_params, return_annotation=return_param.annotation)
    else:
        return inspect.Signature(typed_params)


def get_path_param_names(path: str) -> Set[str]:
    return set(re.findall("{(.*?)}", path))


def get_dependant(
    *,
    path: str,
    call: Callable[..., Any],
    name: Optional[str] = None,
) -> Dependant:
    path_param_names = get_path_param_names(path)
    endpoint_signature = get_typed_signature(call)
    signature_params = endpoint_signature.parameters
    dependant = Dependant(
        call=call,
        name=name,
        path=path,
    )

    for param_name, param in signature_params.items():
        is_path_param = param_name in path_param_names
        type_annotation, param_field = analyze_param(
            param_name=param_name,
            annotation=param.annotation,
            value=param.default,
            is_path_param=is_path_param,
        )
        assert param_field is not None

        add_param_to_fields(field=param_field, dependant=dependant)

    return_annotation = endpoint_signature.return_annotation
    if return_annotation is not inspect.Signature.empty:
        type_annotation, param_field = analyze_param(
            param_name="Return",
            annotation=return_annotation,
            value=None,
            is_path_param=False,
        )
        assert param_field is not None

        dependant.return_param = param_field

    return dependant
