import functools
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)


class MetricsProviderBase(ABC):
    """Class for metric provider template

    Use this template to create your own metric provider.

    """

    # General add metric function. Should return combined metrics Dict
    @abstractmethod
    def add_metric(self, *args, **kwargs):
        pass

    # serialize and return dict for flushing
    @abstractmethod
    def serialize(self, *args, **kwargs):
        pass

    # flush serialized data to output, or send to API directly
    @abstractmethod
    def flush(self, *args, **kwargs):
        pass


class MetricsBase(ABC):
    """Class for metric template

    Use this template to create your own metric class.

    """

    @abstractmethod
    def add_metric(self, *args, **kwargs):
        pass

    @abstractmethod
    def flush_metrics(self, raise_on_empty_metrics: bool = False) -> None:
        pass

    def log_metrics(
        self,
        lambda_handler: Union[Callable[[Dict, Any], Any], Optional[Callable[[Dict, Any, Optional[Dict]], Any]]] = None,
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
        self.add_metric(name="ColdStart", value=1)

        is_cold_start = False
