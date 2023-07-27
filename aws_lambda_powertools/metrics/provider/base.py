from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Dict, Optional

from typing_extensions import Protocol

logger = logging.getLogger(__name__)

is_cold_start = True


class MetricsProviderBase(Protocol):
    """
    Class for metric provider template.

    This class serves as a template for creating your own metric provider. Inherit from this class
    and implement the required methods to define your specific metric provider.

    Usage:
        1. Inherit from this class.
        2. Implement the required methods specific to your metric provider.
        3. Customize the behavior and functionality of the metric provider in your subclass.
    """

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

    def serialize(self, *args: Any, **kwargs: Any) -> Any:
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

    # flush serialized data to output, or send to API directly
    def flush(self, *args: Any, **kwargs) -> Any:
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


class MetricsBase(Protocol):
    """
    Class for metric template.

    This class serves as a template for creating your own metric class. Inherit from this class
    and implement the necessary methods to define your specific metric.

    NOTE: need to improve this docstring
    """

    def add_metric(self, *args, **kwargs):
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

    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        """Manually flushes the metrics. This is normally not necessary,
        unless you're running on other runtimes besides Lambda, where the @log_metrics
        decorator already handles things for you.

        Parameters
        ----------
        raise_on_empty_metrics : bool, optional
            raise exception if no metrics are emitted, by default False
        """
        raise NotImplementedError

    def add_cold_start_metric(self, metric_name: str, function_name: str) -> None:
        """
        Add a cold start metric for a specific function.

        Parameters
        ----------
        metric_name: str
            The name of the cold start metric to add.
        function_name: str
            The name of the function associated with the cold start metric.
        """
        raise NotImplementedError

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
