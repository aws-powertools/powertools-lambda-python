import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.validation.schemas import DynamoDBSchema, EventBridgeSchema

logger = logging.getLogger(__name__)


class Envelope(ABC):
    def _parse_user_dict_schema(self, user_event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        logger.debug("parsing user dictionary schema")
        try:
            return inbound_schema_model(**user_event)
        except (ValidationError, TypeError):
            logger.exception("Valdation exception while extracting user custom schema")
            raise

    def _parse_user_json_string_schema(self, user_event: str, inbound_schema_model: BaseModel) -> Any:
        logger.debug("parsing user dictionary schema")
        try:
            return inbound_schema_model.parse_raw(user_event)
        except (ValidationError, TypeError):
            logger.exception("Valdation exception while extracting user custom schema")
            raise

    @abstractmethod
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        return NotImplemented


class UserEnvelope(Envelope):
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        try:
            return inbound_schema_model(**event)
        except (ValidationError, TypeError):
            logger.exception("Valdation exception received from input user custom envelope event")
            raise


class EventBridgeEnvelope(Envelope):
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        try:
            parsed_envelope = EventBridgeSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Valdation exception received from input eventbridge event")
            raise
        return self._parse_user_dict_schema(parsed_envelope.detail, inbound_schema_model)


class DynamoDBEnvelope(Envelope):
    def parse(self, event: Dict[str, Any], inbound_schema_model: BaseModel) -> Any:
        try:
            parsed_envelope = DynamoDBSchema(**event)
        except (ValidationError, TypeError):
            logger.exception("Valdation exception received from input dynamodb stream event")
            raise
        output = []
        for record in parsed_envelope.Records:
            parsed_new_image = (
                {}
                if not record.dynamodb.NewImage
                else self._parse_user_dict_schema(record.dynamodb.NewImage, inbound_schema_model)
            )  # noqa: E501
            parsed_old_image = (
                {}
                if not record.dynamodb.OldImage
                else self._parse_user_dict_schema(record.dynamodb.OldImage, inbound_schema_model)
            )  # noqa: E501
            output.append({"new": parsed_new_image, "old": parsed_old_image})
        return output


@lambda_handler_decorator
def validator(
    handler: Callable[[Dict, Any], Any],
    event: Dict[str, Any],
    context: Dict[str, Any],
    inbound_schema_model: BaseModel,
    outbound_schema_model: BaseModel,
    envelope: Envelope,
) -> Any:
    """Decorator to create validation for lambda handlers events - both inbound and outbound

        As Lambda follows (event, context) signature we can remove some of the boilerplate
        and also capture any exception any Lambda function throws or its response as metadata

        Example
        -------
        **Lambda function using validation decorator**

            @validator(inbound=inbound_schema_model, outbound=outbound_schema_model)
            def handler(parsed_event_model, context):
                ...

        Parameters
        ----------
        todo add

        Raises
        ------
        err
            TypeError or pydantic.ValidationError or any exception raised by the lambda handler itself
    """
    lambda_handler_name = handler.__name__
    logger.debug("Validating inbound schema")
    parsed_event_model = envelope.parse(event, inbound_schema_model)
    try:
        logger.debug(f"Calling handler {lambda_handler_name}")
        response = handler({"orig": event, "custom": parsed_event_model}, context)
        logger.debug("Received lambda handler response successfully")
        logger.debug(response)
    except Exception:
        logger.exception(f"Exception received from {lambda_handler_name}")
        raise

    try:
        logger.debug("Validating outbound response schema")
        outbound_schema_model(**response)
    except (ValidationError, TypeError):
        logger.exception(f"Validation exception received from {lambda_handler_name} response event")
        raise
    return response
