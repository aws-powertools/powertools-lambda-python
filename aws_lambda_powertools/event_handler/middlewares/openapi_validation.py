import dataclasses
import json
import logging
from copy import deepcopy
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import Route
from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler, NextMiddleware
from aws_lambda_powertools.event_handler.openapi.compat import (
    ModelField,
    _model_dump,
    _normalize_errors,
    _regenerate_error_with_loc,
    get_missing_field_error,
)
from aws_lambda_powertools.event_handler.openapi.encoders import jsonable_encoder
from aws_lambda_powertools.event_handler.openapi.exceptions import RequestValidationError
from aws_lambda_powertools.event_handler.openapi.params import Param
from aws_lambda_powertools.event_handler.openapi.types import IncEx
from aws_lambda_powertools.event_handler.types import EventHandlerInstance

logger = logging.getLogger(__name__)


class OpenAPIValidationMiddleware(BaseMiddlewareHandler):
    def __init__(self):
        super().__init__()

    def handler(self, app: EventHandlerInstance, next_middleware: NextMiddleware) -> Response:
        logger.debug("OpenAPIValidationMiddleware handler")

        route: Route = app.context["_route"]

        values: Dict[str, Any] = {}
        errors: List[Any] = []

        try:
            path_values, path_errors = self._request_params_to_args(
                route.dependant.path_params,
                app.context["_route_args"],
            )
            query_values, query_errors = self._request_params_to_args(
                route.dependant.query_params,
                app.current_event.query_string_parameters or {},
            )

            values.update(path_values)
            values.update(query_values)

            errors += path_errors + query_errors

            if route.dependant.body_params:
                (body_values, body_errors) = self._request_body_to_args(
                    required_params=route.dependant.body_params,
                    received_body=self._get_body(app, route),
                )
                values.update(body_values)
                errors.extend(body_errors)

            if errors:
                raise RequestValidationError(_normalize_errors(errors))
            else:
                app.context["_route_args"] = values
                response = next_middleware(app)

                raw_response = jsonable_encoder(response.body)
                return self._serialize_response(field=route.dependant.return_param, response_content=raw_response)
        except RequestValidationError as e:
            return Response(
                status_code=422,
                content_type="application/json",
                body=json.dumps({"detail": e.errors()}),
            )

    def _serialize_response(
        self,
        *,
        field: Optional[ModelField] = None,
        response_content: Any,
        include: Optional[IncEx] = None,
        exclude: Optional[IncEx] = None,
        by_alias: bool = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Any:
        if field:
            errors = []
            # MAINTENANCE: remove this when we drop pydantic v1
            if not hasattr(field, "serializable"):
                response_content = self._prepare_response_content(
                    response_content,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                )

            value, errors_ = field.validate(response_content, {}, loc=("response",))

            if isinstance(errors_, list):
                errors.extend(errors_)
            elif errors_:
                errors.append(errors_)

            if errors:
                raise RequestValidationError(errors=_normalize_errors(errors), body=response_content)

            if hasattr(field, "serialize"):
                return field.serialize(
                    value,
                    include=include,
                    exclude=exclude,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                )

            return jsonable_encoder(
                value,
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        else:
            return jsonable_encoder(response_content)

    def _prepare_response_content(
        self,
        res: Any,
        *,
        exclude_unset: bool,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Any:
        if isinstance(res, BaseModel):
            return _model_dump(
                res,
                by_alias=True,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        elif isinstance(res, list):
            return [
                self._prepare_response_content(item, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults)
                for item in res
            ]
        elif isinstance(res, dict):
            return {
                k: self._prepare_response_content(v, exclude_unset=exclude_unset, exclude_defaults=exclude_defaults)
                for k, v in res.items()
            }
        elif dataclasses.is_dataclass(res):
            return dataclasses.asdict(res)
        return res

    def _get_body(self, app: EventHandlerInstance, route: Route) -> Dict[str, Any]:
        content_type_value = app.current_event.get_header_value("content-type")
        if not content_type_value or content_type_value.startswith("application/json"):
            try:
                return app.current_event.json_body
            except json.JSONDecodeError as e:
                raise RequestValidationError(
                    [
                        {
                            "type": "json_invalid",
                            "loc": ("body", e.pos),
                            "msg": "JSON decode error",
                            "input": {},
                            "ctx": {"error": e.msg},
                        },
                    ],
                    body=e.doc,
                ) from e
        else:
            raise NotImplementedError("Only JSON body is supported")

    @staticmethod
    def _request_params_to_args(
        required_params: Sequence[ModelField],
        received_params: Mapping[str, Any],
    ) -> Tuple[Dict[str, Any], List[Any]]:
        values = {}
        errors = []

        for field in required_params:
            value = received_params.get(field.alias)

            field_info = field.field_info
            if not isinstance(field_info, Param):
                raise AssertionError(f"Expected Param field_info, got {field_info}")

            loc = (field_info.in_.value, field.alias)
            if value is None:
                if field.required:
                    errors.append(get_missing_field_error(loc=loc))
                else:
                    values[field.name] = deepcopy(field.default)
                continue

            _validate_field(field=field, value=value, loc=loc, existing_values=values, existing_errors=errors)

        return values, errors

    @staticmethod
    def _request_body_to_args(
        required_params: List[ModelField],
        received_body: Optional[Dict[str, Any]],
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        values: Dict[str, Any] = {}
        errors: List[Dict[str, Any]] = []

        if not required_params:
            return values, errors

        received_body, field_alias_omitted = _get_embed_body(
            field=required_params[0],
            required_params=required_params,
            received_body=received_body,
        )

        for field in required_params:
            loc: Tuple[str, ...] = ("body", field.alias)
            if field_alias_omitted:
                loc = ("body",)

            value: Optional[Any] = None

            if received_body is not None:
                try:
                    value = received_body.get(field.alias)
                except AttributeError:
                    errors.append(get_missing_field_error(loc))
                    continue

            # Determine if the field is required
            if value is None:
                if field.required:
                    errors.append(get_missing_field_error(loc))
                else:
                    values[field.name] = deepcopy(field.default)
                continue

            # MAINTENANCE: Handle byte and file fields

            _validate_field(field=field, value=value, loc=loc, existing_values=values, existing_errors=errors)

        return values, errors


def _validate_field(
    *,
    field: ModelField,
    value: Any,
    loc: Tuple[str, ...],
    existing_values: Dict[str, Any],
    existing_errors: List[Dict[str, Any]],
):
    validated_value, errors = field.validate(value, existing_values, loc=loc)

    if isinstance(errors, list):
        processed_errors = _regenerate_error_with_loc(errors=errors, loc_prefix=())
        existing_errors.extend(processed_errors)
    elif errors:
        existing_errors.append(errors)
    else:
        existing_values[field.name] = validated_value


def _get_embed_body(
    *,
    field: ModelField,
    required_params: List[ModelField],
    received_body: Optional[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], bool]:
    field_info = field.field_info
    embed = getattr(field_info, "embed", None)

    field_alias_omitted = len(required_params) == 1 and not embed
    if field_alias_omitted:
        received_body = {field.alias: received_body}

    return received_body, field_alias_omitted
