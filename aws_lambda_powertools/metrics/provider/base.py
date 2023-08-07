from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Dict, Optional

from typing_extensions import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

is_cold_start = True


@runtime_checkable
class MetricsProviderBase(Protocol):
    """
    Interface for MetricsProvider.

    This class serves as an interface for creating your own metric provider. Inherit from this class
    and implement the required methods to define your specific metric provider.

    Usage:
        1. Inherit from this class.
        2. Implement the required methods specific to your metric provider.
        3. Customize the behavior and functionality of the metric provider in your subclass.
    """

    def add_metric(self, *args: Any, **kwargs: Any) -> Any:
        ...

    def serialize_metric_set(self, *args: Any, **kwargs: Any) -> Any:
        ...

    def flush_metrics(self, *args: Any, **kwargs) -> Any:
        ...


@runtime_checkable
class MetricsBase(Protocol):
    """
    Interface for metric template.

    This class serves as a template for creating your own metric class. Inherit from this class
    and implement the necessary methods to define your specific metric.

    NOTE: need to improve this docstring
    """

    def add_metric(self, *args, **kwargs):
        ...

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        ...

    def add_cold_start_metric(self, metric_name: str, function_name: str) -> None:
        ...

    def log_metrics(
        self,
        lambda_handler: Callable[[Dict, Any], Any] | Optional[Callable[[Dict, Any, Optional[Dict]], Any]] = None,
        capture_cold_start_metric: bool = False,
        raise_on_empty_metrics: bool = False,
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

        # If handler is None we've been called with parameters
        # Return a partial function with args filled
        if lambda_handler is None:
            logger.debug("Decorator called with parameters")
            return functools.partial(
                self.log_metrics,
                capture_cold_start_metric=capture_cold_start_metric,
                raise_on_empty_metrics=raise_on_empty_metrics,
            )

        @functools.wraps(lambda_handler)
        def decorate(event, context):
            try:
                response = lambda_handler(event, context)
                if capture_cold_start_metric:
                    self._add_cold_start_metric(context=context)
            finally:
                self.flush_metrics(raise_on_empty_metrics=raise_on_empty_metrics)

            return response

        return decorate

    def _add_cold_start_metric(self, context: Any) -> None:
        """Add cold start metric and function_name dimension

        Parameters
        ----------
        context : Any
            Lambda context
        """
        global is_cold_start
        if not is_cold_start:
            return

        logger.debug("Adding cold start metric and function_name dimension")
        self.add_cold_start_metric(metric_name="ColdStart", function_name=context.function_name)

        is_cold_start = False


def reset_cold_start_flag_provider():
    global is_cold_start
    if not is_cold_start:
        is_cold_start = True
