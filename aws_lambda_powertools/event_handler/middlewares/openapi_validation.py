import dataclasses
import json
import logging
from copy import deepcopy
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from pydantic import BaseModel

from aws_lambda_powertools.event_handler import (
    ALBResolver,
    APIGatewayHttpResolver,
    APIGatewayRestResolver,
    LambdaFunctionUrlResolver,
    Response,
    VPCLatticeV2Resolver,
)
from aws_lambda_powertools.event_handler.api_gateway import Route
from aws_lambda_powertools.event_handler.middlewares import BaseMiddlewareHandler, NextMiddleware
from aws_lambda_powertools.event_handler.openapi.compat import (
    ModelField,
    _model_dump,
    _normalize_errors,
    _regenerate_error_with_loc,
    get_missing_field_error,
)
from aws_lambda_powertools.event_handler.openapi.dependant import is_scalar_field
from aws_lambda_powertools.event_handler.openapi.encoders import jsonable_encoder
from aws_lambda_powertools.event_handler.openapi.exceptions import RequestValidationError
from aws_lambda_powertools.event_handler.openapi.params import Param
from aws_lambda_powertools.event_handler.openapi.types import IncEx
from aws_lambda_powertools.event_handler.types import EventHandlerInstance

logger = logging.getLogger(__name__)


class OpenAPIValidationMiddleware(BaseMiddlewareHandler):
    """
    OpenAPIValidationMiddleware is a middleware that validates the request against the OpenAPI schema defined by the
    Lambda handler. It also validates the response against the OpenAPI schema defined by the Lambda handler. It
    should not be used directly, but rather through the `enable_validation` parameter of the `ApiGatewayResolver`.

    Examples
    --------

    ```python
    from typing import List

    from pydantic import BaseModel

    from aws_lambda_powertools.event_handler.api_gateway import (
        APIGatewayRestResolver,
    )

    class Todo(BaseModel):
      name: str

    app = APIGatewayRestResolver(enable_validation=True)

    @app.get("/todos")
    def get_todos(): List[Todo]:
      return [Todo(name="hello world")]
    ```
    """

    def _extract_multi_query_string_with_param(self, query_string, params: Sequence[ModelField]):
        """
        Extract and process multi_query_string_parameters for VPCLatticeV2Resolver and APIGatewayRestResolver.

        Parameters
        ----------
        query_string: Dict
            A dictionary containing the initial query string parameters.
        params: Sequence[ModelField]
            A sequence of ModelField objects representing parameters.

        Returns
        -------
        A dictionary containing the processed multi_query_string_parameters.

        Comments
        --------
        - This method is specifically designed for VPCLatticeV2Resolver and APIGatewayRestResolver.
        - It processes multi_query_string_parameters based on the given params.
        """
        for param in filter(is_scalar_field, params):
            try:
                # If the field is a scalar, it implies it's not a multi-query string.
                # And we keep the first value for this field

                # We Attempt to retain only the first element if the parameter is a scalar field
                query_string[param.name] = query_string[param.name][0]
            except KeyError:
                pass
        return query_string

    def _extract_query_string(self, app: EventHandlerInstance, params: Sequence[ModelField]):
        """
        Extract and process query string parameters based on the resolver type.
        Payloads are different and we need to identify when it is using multiValueQueryStringParameters.

        References
        https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html#http-api-develop-integrations-lambda.proxy-format
        https://docs.aws.amazon.com/elasticloadbalancing/latest/application/lambda-functions.html#multi-value-headers
        https://docs.aws.amazon.com/vpc-lattice/latest/ug/lambda-functions.html#multi-value-headers
        https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html#urls-payloads

        Parameters
        ----------
        app: EventHandlerInstance.
            Instance of a Resolver
        params: Sequence[ModelField]
            A sequence of ModelField objects representing parameters.

        Returns
        -------
            A dictionary containing the processed query string parameters.

        Comments
        --------
        - The initial query is obtained from app.current_event.query_string_parameters.

        - In the case of using LambdaFunctionUrlResolver or APIGatewayHttpResolver, multi-query strings consistently
          reside in the same field, separated by commas. Consequently, we split these strings into lists.

        - When using a VPCLatticeV2Resolver, the Payload consistently sends query strings as arrays. To enhance
          compatibility, we attempt to identify scalar types within the arrays and convert them to single elements.

        - In the case of using APIGatewayRestResolver or ALBResolver, the payload may includes both query string and
          multi-query string fields. We apply a similar logic as used in VPCLatticeV2Resolver
          to handle these query strings effectively.

        - VPCLatticeResolver (v1) and BedrockAgentResolver doesn't support multi-query strings
          and we retain original query_string field
        """

        query_string = app.current_event.query_string_parameters or {}

        if isinstance(app, (LambdaFunctionUrlResolver, APIGatewayHttpResolver)):
            query_string = {key: value.split(",") if "," in value else value for key, value in query_string.items()}

        if isinstance(app, VPCLatticeV2Resolver):
            query_string = self._extract_multi_query_string_with_param(query_string, params)

        if (
            isinstance(app, (ALBResolver, APIGatewayRestResolver))
            and app.current_event.multi_value_query_string_parameters
        ):
            query_string = self._extract_multi_query_string_with_param(
                app.current_event.multi_value_query_string_parameters,
                params,
            )

        return query_string

    def handler(self, app: EventHandlerInstance, next_middleware: NextMiddleware) -> Response:
        logger.debug("OpenAPIValidationMiddleware handler")

        route: Route = app.context["_route"]

        values: Dict[str, Any] = {}
        errors: List[Any] = []

        # Process path values, which can be found on the route_args
        path_values, path_errors = _request_params_to_args(
            route.dependant.path_params,
            app.context["_route_args"],
        )

        query_string = self._extract_query_string(app, route.dependant.query_params)

        # Process query values
        query_values, query_errors = _request_params_to_args(
            route.dependant.query_params,
            query_string,
        )

        values.update(path_values)
        values.update(query_values)
        errors += path_errors + query_errors

        # Process the request body, if it exists
        if route.dependant.body_params:
            (body_values, body_errors) = _request_body_to_args(
                required_params=route.dependant.body_params,
                received_body=self._get_body(app),
            )
            values.update(body_values)
            errors.extend(body_errors)

        if errors:
            # Raise the validation errors
            raise RequestValidationError(_normalize_errors(errors))
        else:
            # Re-write the route_args with the validated values, and call the next middleware
            app.context["_route_args"] = values

            # Call the handler by calling the next middleware
            response = next_middleware(app)

            # Process the response
            return self._handle_response(route=route, response=response)

    def _handle_response(self, *, route: Route, response: Response):
        # Process the response body if it exists
        if response.body:
            # Validate and serialize the response, if it's JSON
            if response.is_json():
                response.body = self._serialize_response(
                    field=route.dependant.return_param,
                    response_content=response.body,
                )

        return response

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
        """
        Serialize the response content according to the field type.
        """
        if field:
            errors: List[Dict[str, Any]] = []
            # MAINTENANCE: remove this when we drop pydantic v1
            if not hasattr(field, "serializable"):
                response_content = self._prepare_response_content(
                    response_content,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                )

            value = _validate_field(field=field, value=response_content, loc=("response",), existing_errors=errors)
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
            # Just serialize the response content returned from the handler
            return jsonable_encoder(response_content)

    def _prepare_response_content(
        self,
        res: Any,
        *,
        exclude_unset: bool,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Any:
        """
        Prepares the response content for serialization.
        """
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

    def _get_body(self, app: EventHandlerInstance) -> Dict[str, Any]:
        """
        Get the request body from the event, and parse it as JSON.
        """

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


def _request_params_to_args(
    required_params: Sequence[ModelField],
    received_params: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[Any]]:
    """
    Convert the request params to a dictionary of values using validation, and returns a list of errors.
    """
    values = {}
    errors = []

    for field in required_params:
        value = received_params.get(field.alias)

        field_info = field.field_info
        if not isinstance(field_info, Param):
            raise AssertionError(f"Expected Param field_info, got {field_info}")

        loc = (field_info.in_.value, field.alias)

        # If we don't have a value, see if it's required or has a default
        if value is None:
            if field.required:
                errors.append(get_missing_field_error(loc=loc))
            else:
                values[field.name] = deepcopy(field.default)
            continue

        # Finally, validate the value
        values[field.name] = _validate_field(field=field, value=value, loc=loc, existing_errors=errors)

    return values, errors


def _request_body_to_args(
    required_params: List[ModelField],
    received_body: Optional[Dict[str, Any]],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Convert the request body to a dictionary of values using validation, and returns a list of errors.
    """
    values: Dict[str, Any] = {}
    errors: List[Dict[str, Any]] = []

    received_body, field_alias_omitted = _get_embed_body(
        field=required_params[0],
        required_params=required_params,
        received_body=received_body,
    )

    for field in required_params:
        # This sets the location to:
        # { "user": { object } } if field.alias == user
        # { { object } if field_alias is omitted
        loc: Tuple[str, ...] = ("body", field.alias)
        if field_alias_omitted:
            loc = ("body",)

        value: Optional[Any] = None

        # Now that we know what to look for, try to get the value from the received body
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

        # Finally, validate the value
        values[field.name] = _validate_field(field=field, value=value, loc=loc, existing_errors=errors)

    return values, errors


def _validate_field(
    *,
    field: ModelField,
    value: Any,
    loc: Tuple[str, ...],
    existing_errors: List[Dict[str, Any]],
):
    """
    Validate a field, and append any errors to the existing_errors list.
    """
    validated_value, errors = field.validate(value, value, loc=loc)

    if isinstance(errors, list):
        processed_errors = _regenerate_error_with_loc(errors=errors, loc_prefix=())
        existing_errors.extend(processed_errors)
    elif errors:
        existing_errors.append(errors)

    return validated_value


def _get_embed_body(
    *,
    field: ModelField,
    required_params: List[ModelField],
    received_body: Optional[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], bool]:
    field_info = field.field_info
    embed = getattr(field_info, "embed", None)

    # If the field is an embed, and the field alias is omitted, we need to wrap the received body in the field alias.
    field_alias_omitted = len(required_params) == 1 and not embed
    if field_alias_omitted:
        received_body = {field.alias: received_body}

    return received_body, field_alias_omitted
