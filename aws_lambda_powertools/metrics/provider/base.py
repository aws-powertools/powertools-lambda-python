from __future__ import annotations

import functools
import logging
from abc import ABC, abstractmethod
from typing import Any

from aws_lambda_powertools.metrics.provider import cold_start
from aws_lambda_powertools.shared.types import AnyCallableT
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """
    Interface to create a metrics provider.

    BaseProvider implements `log_metrics` decorator for every provider as a value add feature.

    Usage:
        1. Inherit from this class.
        2. Implement the required methods specific to your metric provider.
        3. Customize the behavior and functionality of the metric provider in your subclass.
    """

    @abstractmethod
    def add_metric(self, *args: Any, **kwargs: Any) -> Any:
        """
        Abstract method for adding a metric.

        This method must be implemented in subclasses to add a metric and return a combined metrics dictionary.

        Parameters
        ----------
        *args:
            Positional arguments.
        *kwargs:
            Keyword arguments.

        Returns
        ----------
        Dict
            A combined metrics dictionary.

        Raises
        ----------
        NotImplementedError
            This method must be implemented in subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def serialize_metric_set(self, *args: Any, **kwargs: Any) -> Any:
        """
        Abstract method for serialize a metric.

        This method must be implemented in subclasses to add a metric and return a combined metrics dictionary.

        Parameters
        ----------
        *args:
            Positional arguments.
        *kwargs:
            Keyword arguments.

        Returns
        ----------
        Dict
            Serialized metrics

        Raises
        ----------
        NotImplementedError
            This method must be implemented in subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def flush_metrics(self, *args: Any, **kwargs) -> Any:
        """
        Abstract method for flushing a metric.

        This method must be implemented in subclasses to add a metric and return a combined metrics dictionary.

        Parameters
        ----------
        *args:
            Positional arguments.
        *kwargs:
            Keyword arguments.

        Raises
        ----------
        NotImplementedError
            This method must be implemented in subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def clear_metrics(self, *args: Any, **kwargs) -> None:
        """
        Abstract method for clear metric instance.

        This method must be implemented in subclasses to clear the metric instance

        Parameters
        ----------
        *args:
            Positional arguments.
        *kwargs:
            Keyword arguments.

        Raises
        ----------
        NotImplementedError
            This method must be implemented in subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def add_cold_start_metric(self, context: LambdaContext) -> Any:
        """
        Abstract method for clear metric instance.

        This method must be implemented in subclasses to add a metric and return a combined metrics dictionary.

        Parameters
        ----------
        *args:
            Positional arguments.
        *kwargs:
            Keyword arguments.

        Raises
        ----------
        NotImplementedError
            This method must be implemented in subclasses.
        """
        raise NotImplementedError

    def log_metrics(
        self,
        lambda_handler: AnyCallableT | None = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
        **kwargs,
    ):
        """Decorator to serialize and publish metrics at the end of a function execution.

        Be aware that the log_metrics **does call* the decorated function (e.g. lambda_handler).

        Example
        -------
        **Lambda function using tracer and metrics decorators**

            from aws_lambda_powertools import Metrics, Tracer

            metrics = Metrics(service="payment")
            tracer = Tracer(service="payment")

            @tracer.capture_lambda_handler
            @metrics.log_metrics
            def handler(event, context):
                    ...

        Parameters
        ----------
        lambda_handler : Callable[[Any, Any], Any], optional
            lambda function handler, by default None
        capture_cold_start_metric : bool, optional
            captures cold start metric, by default False
        raise_on_empty_metrics : bool, optional
            raise exception if no metrics are emitted, by default False
        default_dimensions: Dict[str, str], optional
            metric dimensions as key=value that will always be present

        Raises
        ------
        e
            Propagate error received
        """
        extra_args = {}

        if kwargs.get("default_dimensions"):
            extra_args.update({"default_dimensions": kwargs.get("default_dimensions")})

        if kwargs.get("default_tags"):
            extra_args.update({"default_tags": kwargs.get("default_tags")})

        # If handler is None we've been called with parameters
        # Return a partial function with args filled
        if lambda_handler is None:
            logger.debug("Decorator called with parameters")
            return functools.partial(
                self.log_metrics,
                capture_cold_start_metric=capture_cold_start_metric,
                raise_on_empty_metrics=raise_on_empty_metrics,
                **extra_args,
            )

        @functools.wraps(lambda_handler)
        def decorate(event, context, *args, **kwargs):
            try:
                response = lambda_handler(event, context, *args, **kwargs)
                if capture_cold_start_metric:
                    self._add_cold_start_metric(context=context)
            finally:
                self.flush_metrics(raise_on_empty_metrics=raise_on_empty_metrics)

            return response

        return decorate

    def _add_cold_start_metric(self, context: Any) -> None:
        """
        Add cold start metric

        Parameters
        ----------
        context : Any
            Lambda context
        """
        if not cold_start.is_cold_start:
            return

        logger.debug("Adding cold start metric and function_name dimension")
        self.add_cold_start_metric(context=context)

        cold_start.is_cold_start = False


def reset_cold_start_flag_provider():
    if not cold_start.is_cold_start:
        cold_start.is_cold_start = True
