import contextlib
import copy
import functools
import inspect
import logging
import numbers
import os
from typing import Any, Callable, Dict, List, Optional, Sequence, Union, cast, overload

from ..shared import constants
from ..shared.functions import resolve_env_var_choice, resolve_truthy_env_var_choice
from ..shared.lazy_import import LazyLoader
from ..shared.types import AnyCallableT
from .base import BaseProvider, BaseSegment

is_cold_start = True
logger = logging.getLogger(__name__)

aws_xray_sdk = LazyLoader(constants.XRAY_SDK_MODULE, globals(), constants.XRAY_SDK_MODULE)


class Tracer:
    """Tracer using AWS-XRay to provide decorators with known defaults for Lambda functions

    When running locally, it detects whether it's running via SAM CLI,
    and if it is it returns dummy segments/subsegments instead.

    By default, it patches all available libraries supported by X-Ray SDK. Patching is
    automatically disabled when running locally via SAM CLI or by any other means. \n
    Ref: https://docs.aws.amazon.com/xray-sdk-for-python/latest/reference/thirdparty.html

    Tracer keeps a copy of its configuration as it can be instantiated more than once. This
    is useful when you are using your own middlewares and want to utilize an existing Tracer.
    Make sure to set `auto_patch=False` in subsequent Tracer instances to avoid double patching.

    Environment variables
    ---------------------
    POWERTOOLS_TRACE_DISABLED : str
        disable tracer (e.g. `"true", "True", "TRUE"`)
    POWERTOOLS_SERVICE_NAME : str
        service name
    POWERTOOLS_TRACER_CAPTURE_RESPONSE : str
        disable auto-capture response as metadata (e.g. `"true", "True", "TRUE"`)
    POWERTOOLS_TRACER_CAPTURE_ERROR : str
        disable auto-capture error as metadata (e.g. `"true", "True", "TRUE"`)

    Parameters
    ----------
    service: str
        Service name that will be appended in all tracing metadata
    auto_patch: bool
        Patch existing imported modules during initialization, by default True
    disabled: bool
        Flag to explicitly disable tracing, useful when running/testing locally
        `Env POWERTOOLS_TRACE_DISABLED="true"`
    patch_modules: Optional[Sequence[str]]
        Tuple of modules supported by tracing provider to patch, by default all modules are patched
    provider: BaseProvider
        Tracing provider, by default it is aws_xray_sdk.core.xray_recorder

    Returns
    -------
    Tracer
        Tracer instance with imported modules patched

    Example
    -------
    **A Lambda function using Tracer**

        from aws_lambda_powertools import Tracer
        tracer = Tracer(service="greeting")

        @tracer.capture_method
        def greeting(name: str) -> Dict:
            return {
                "name": name
            }

        @tracer.capture_lambda_handler
        def handler(event: dict, context: Any) -> Dict:
            print("Received event from Lambda...")
            response = greeting(name="Heitor")
            return response

    **Booking Lambda function using Tracer that adds additional annotation/metadata**

        from aws_lambda_powertools import Tracer
        tracer = Tracer(service="booking")

        @tracer.capture_method
        def confirm_booking(booking_id: str) -> Dict:
                resp = add_confirmation(booking_id)

                tracer.put_annotation("BookingConfirmation", resp["requestId"])
                tracer.put_metadata("Booking confirmation", resp)

                return resp

        @tracer.capture_lambda_handler
        def handler(event: dict, context: Any) -> Dict:
            print("Received event from Lambda...")
            booking_id = event.get("booking_id")
            response = confirm_booking(booking_id=booking_id)
            return response

    **A Lambda function using service name via POWERTOOLS_SERVICE_NAME**

        export POWERTOOLS_SERVICE_NAME="booking"
        from aws_lambda_powertools import Tracer
        tracer = Tracer()

        @tracer.capture_lambda_handler
        def handler(event: dict, context: Any) -> Dict:
            print("Received event from Lambda...")
            response = greeting(name="Lessa")
            return response

    **Reuse an existing instance of Tracer anywhere in the code**

        # lambda_handler.py
        from aws_lambda_powertools import Tracer
        tracer = Tracer()

        @tracer.capture_lambda_handler
        def handler(event: dict, context: Any) -> Dict:
            ...

        # utils.py
        from aws_lambda_powertools import Tracer
        tracer = Tracer()
        ...

    Limitations
    -----------
    * Async handler not supported
    """

    _default_config: Dict[str, Any] = {
        "service": "",
        "disabled": False,
        "auto_patch": True,
        "patch_modules": None,
        "provider": None,
    }
    _config = copy.copy(_default_config)

    def __init__(
        self,
        service: Optional[str] = None,
        disabled: Optional[bool] = None,
        auto_patch: Optional[bool] = None,
        patch_modules: Optional[Sequence[str]] = None,
        provider: Optional[BaseProvider] = None,
    ):
        self.__build_config(
            service=service,
            disabled=disabled,
            auto_patch=auto_patch,
            patch_modules=patch_modules,
            provider=provider,
        )
        self.provider: BaseProvider = self._config["provider"]
        self.disabled = self._config["disabled"]
        self.service = self._config["service"]
        self.auto_patch = self._config["auto_patch"]

        if self.disabled:
            self._disable_tracer_provider()

        if self.auto_patch:
            self.patch(modules=patch_modules)

        if self._is_xray_provider():
            self._disable_xray_trace_batching()

    def put_annotation(self, key: str, value: Union[str, numbers.Number, bool]):
        """Adds annotation to existing segment or subsegment

        Parameters
        ----------
        key : str
            Annotation key
        value : Union[str, numbers.Number, bool]
            Value for annotation

        Example
        -------
        Custom annotation for a pseudo service named payment

            tracer = Tracer(service="payment")
            tracer.put_annotation("PaymentStatus", "CONFIRMED")
        """
        if self.disabled:
            logger.debug("Tracing has been disabled, aborting put_annotation")
            return

        logger.debug(f"Annotating on key '{key}' with '{value}'")
        self.provider.put_annotation(key=key, value=value)

    def put_metadata(self, key: str, value: Any, namespace: Optional[str] = None):
        """Adds metadata to existing segment or subsegment

        Parameters
        ----------
        key : str
            Metadata key
        value : any
            Value for metadata
        namespace : str, optional
            Namespace that metadata will lie under, by default None

        Example
        -------
        Custom metadata for a pseudo service named payment

            tracer = Tracer(service="payment")
            response = collect_payment()
            tracer.put_metadata("Payment collection", response)
        """
        if self.disabled:
            logger.debug("Tracing has been disabled, aborting put_metadata")
            return

        namespace = namespace or self.service
        logger.debug(f"Adding metadata on key '{key}' with '{value}' at namespace '{namespace}'")
        self.provider.put_metadata(key=key, value=value, namespace=namespace)

    def patch(self, modules: Optional[Sequence[str]] = None):
        """Patch modules for instrumentation.

        Patches all supported modules by default if none are given.

        Parameters
        ----------
        modules : Optional[Sequence[str]]
            List of modules to be patched, optional by default
        """
        if self.disabled:
            logger.debug("Tracing has been disabled, aborting patch")
            return

        if modules is None:
            self.provider.patch_all()
        else:
            self.provider.patch(modules)

    def capture_lambda_handler(
        self,
        lambda_handler: Union[Callable[[Dict, Any], Any], Optional[Callable[[Dict, Any, Optional[Dict]], Any]]] = None,
        capture_response: Optional[bool] = None,
        capture_error: Optional[bool] = None,
    ):
        """Decorator to create subsegment for lambda handlers

        As Lambda follows (event, context) signature we can remove some of the boilerplate
        and also capture any exception any Lambda function throws or its response as metadata

        Parameters
        ----------
        lambda_handler : Callable
            Method to annotate on
        capture_response : bool, optional
            Instructs tracer to not include handler's response as metadata
        capture_error : bool, optional
            Instructs tracer to not include handler's error as metadata, by default True

        Example
        -------
        **Lambda function using capture_lambda_handler decorator**

            tracer = Tracer(service="payment")
            @tracer.capture_lambda_handler
            def handler(event, context):
                ...

        **Preventing Tracer to log response as metadata**

            tracer = Tracer(service="payment")
            @tracer.capture_lambda_handler(capture_response=False)
            def handler(event, context):
                ...

        Raises
        ------
        err
            Exception raised by method
        """
        # If handler is None we've been called with parameters
        # Return a partial function with args filled
        if lambda_handler is None:
            logger.debug("Decorator called with parameters")
            return functools.partial(
                self.capture_lambda_handler,
                capture_response=capture_response,
                capture_error=capture_error,
            )

        lambda_handler_name = lambda_handler.__name__
        capture_response = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_RESPONSE_ENV, "true"),
            choice=capture_response,
        )
        capture_error = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_ERROR_ENV, "true"),
            choice=capture_error,
        )

        @functools.wraps(lambda_handler)
        def decorate(event, context, **kwargs):
            with self.provider.in_subsegment(name=f"## {lambda_handler_name}") as subsegment:
                try:
                    logger.debug("Calling lambda handler")
                    response = lambda_handler(event, context, **kwargs)
                    logger.debug("Received lambda handler response successfully")
                    self._add_response_as_metadata(
                        method_name=lambda_handler_name,
                        data=response,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from {lambda_handler_name}")
                    self._add_full_exception_as_metadata(
                        method_name=lambda_handler_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )

                    raise
                finally:
                    global is_cold_start
                    logger.debug("Annotating cold start")
                    subsegment.put_annotation(key="ColdStart", value=is_cold_start)

                    if is_cold_start:
                        is_cold_start = False

                    if self.service:
                        subsegment.put_annotation(key="Service", value=self.service)

                return response

        return decorate

    # see #465
    @overload
    def capture_method(self, method: "AnyCallableT") -> "AnyCallableT":
        ...  # pragma: no cover

    @overload
    def capture_method(
        self,
        method: None = None,
        capture_response: Optional[bool] = None,
        capture_error: Optional[bool] = None,
    ) -> Callable[["AnyCallableT"], "AnyCallableT"]:
        ...  # pragma: no cover

    def capture_method(
        self,
        method: Optional[AnyCallableT] = None,
        capture_response: Optional[bool] = None,
        capture_error: Optional[bool] = None,
    ) -> AnyCallableT:
        """Decorator to create subsegment for arbitrary functions

        It also captures both response and exceptions as metadata
        and creates a subsegment named `## <method_module.method_qualifiedname>`
        # see here: [Qualified name for classes and functions](https://peps.python.org/pep-3155/)

        When running [async functions concurrently](https://docs.python.org/3/library/asyncio-task.html#id6),
        methods may impact each others subsegment, and can trigger
        and AlreadyEndedException from X-Ray due to async nature.

        For this use case, either use `capture_method` only where
        `async.gather` is called, or use `in_subsegment_async`
        context manager via our escape hatch mechanism - See examples.

        Parameters
        ----------
        method : Callable
            Method to annotate on
        capture_response : bool, optional
            Instructs tracer to not include method's response as metadata
        capture_error : bool, optional
            Instructs tracer to not include handler's error as metadata, by default True

        Example
        -------
        **Custom function using capture_method decorator**

            tracer = Tracer(service="payment")
            @tracer.capture_method
            def some_function()

        **Custom async method using capture_method decorator**

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            @tracer.capture_method
            async def confirm_booking(booking_id: str) -> Dict:
                resp = call_to_booking_service()

                tracer.put_annotation("BookingConfirmation", resp["requestId"])
                tracer.put_metadata("Booking confirmation", resp)

                return resp

            def lambda_handler(event: dict, context: Any) -> Dict:
                booking_id = event.get("booking_id")
                asyncio.run(confirm_booking(booking_id=booking_id))

        **Custom generator function using capture_method decorator**

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            @tracer.capture_method
            def bookings_generator(booking_id):
                resp = call_to_booking_service()
                yield resp[0]
                yield resp[1]

            def lambda_handler(event: dict, context: Any) -> Dict:
                gen = bookings_generator(booking_id=booking_id)
                result = list(gen)

        **Custom generator context manager using capture_method decorator**

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            @tracer.capture_method
            @contextlib.contextmanager
            def booking_actions(booking_id):
                resp = call_to_booking_service()
                yield "example result"
                cleanup_stuff()

            def lambda_handler(event: dict, context: Any) -> Dict:
                booking_id = event.get("booking_id")

                with booking_actions(booking_id=booking_id) as booking:
                    result = booking

        **Tracing nested async calls**

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            @tracer.capture_method
            async def get_identity():
                ...

            @tracer.capture_method
            async def long_async_call():
                ...

            @tracer.capture_method
            async def async_tasks():
                await get_identity()
                ret = await long_async_call()

                return { "task": "done", **ret }

        **Safely tracing concurrent async calls with decorator**

        This may not needed once [this bug is closed](https://github.com/aws/aws-xray-sdk-python/issues/164)

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            async def get_identity():
                async with aioboto3.client("sts") as sts:
                    account = await sts.get_caller_identity()
                    return account

            async def long_async_call():
                ...

            @tracer.capture_method
            async def async_tasks():
                _, ret = await asyncio.gather(get_identity(), long_async_call(), return_exceptions=True)

                return { "task": "done", **ret }

        **Safely tracing each concurrent async calls with escape hatch**

        This may not needed once [this bug is closed](https://github.com/aws/aws-xray-sdk-python/issues/164)

            from aws_lambda_powertools import Tracer
            tracer = Tracer(service="booking")

            async def get_identity():
                async tracer.provider.in_subsegment_async("## get_identity"):
                    ...

            async def long_async_call():
                async tracer.provider.in_subsegment_async("## long_async_call"):
                    ...

            @tracer.capture_method
            async def async_tasks():
                _, ret = await asyncio.gather(get_identity(), long_async_call(), return_exceptions=True)

                return { "task": "done", **ret }

        Raises
        ------
        err
            Exception raised by method
        """
        # If method is None we've been called with parameters
        # Return a partial function with args filled
        if method is None:
            logger.debug("Decorator called with parameters")
            return cast(
                AnyCallableT,
                functools.partial(self.capture_method, capture_response=capture_response, capture_error=capture_error),
            )

        # Example: app.ClassA.get_all  # noqa ERA001
        method_name = f"{method.__module__}.{method.__qualname__}"

        capture_response = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_RESPONSE_ENV, "true"),
            choice=capture_response,
        )
        capture_error = resolve_truthy_env_var_choice(
            env=os.getenv(constants.TRACER_CAPTURE_ERROR_ENV, "true"),
            choice=capture_error,
        )

        # Maintenance: Need a factory/builder here to simplify this now
        if inspect.iscoroutinefunction(method):
            return self._decorate_async_function(
                method=method,
                capture_response=capture_response,
                capture_error=capture_error,
                method_name=method_name,
            )
        elif inspect.isgeneratorfunction(method):
            return self._decorate_generator_function(
                method=method,
                capture_response=capture_response,
                capture_error=capture_error,
                method_name=method_name,
            )
        elif hasattr(method, "__wrapped__") and inspect.isgeneratorfunction(method.__wrapped__):
            return self._decorate_generator_function_with_context_manager(
                method=method,
                capture_response=capture_response,
                capture_error=capture_error,
                method_name=method_name,
            )
        else:
            return self._decorate_sync_function(
                method=method,
                capture_response=capture_response,
                capture_error=capture_error,
                method_name=method_name,
            )

    def _decorate_async_function(
        self,
        method: Callable,
        capture_response: Optional[Union[bool, str]] = None,
        capture_error: Optional[Union[bool, str]] = None,
        method_name: Optional[str] = None,
    ):
        @functools.wraps(method)
        async def decorate(*args, **kwargs):
            async with self.provider.in_subsegment_async(name=f"## {method_name}") as subsegment:
                try:
                    logger.debug(f"Calling method: {method_name}")
                    response = await method(*args, **kwargs)
                    self._add_response_as_metadata(
                        method_name=method_name,
                        data=response,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from '{method_name}' method")
                    self._add_full_exception_as_metadata(
                        method_name=method_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )
                    raise

                return response

        return decorate

    def _decorate_generator_function(
        self,
        method: Callable,
        capture_response: Optional[Union[bool, str]] = None,
        capture_error: Optional[Union[bool, str]] = None,
        method_name: Optional[str] = None,
    ):
        @functools.wraps(method)
        def decorate(*args, **kwargs):
            with self.provider.in_subsegment(name=f"## {method_name}") as subsegment:
                try:
                    logger.debug(f"Calling method: {method_name}")
                    result = yield from method(*args, **kwargs)
                    self._add_response_as_metadata(
                        method_name=method_name,
                        data=result,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from '{method_name}' method")
                    self._add_full_exception_as_metadata(
                        method_name=method_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )
                    raise

                return result

        return decorate

    def _decorate_generator_function_with_context_manager(
        self,
        method: Callable,
        capture_response: Optional[Union[bool, str]] = None,
        capture_error: Optional[Union[bool, str]] = None,
        method_name: Optional[str] = None,
    ):
        @functools.wraps(method)
        @contextlib.contextmanager
        def decorate(*args, **kwargs):
            with self.provider.in_subsegment(name=f"## {method_name}") as subsegment:
                try:
                    logger.debug(f"Calling method: {method_name}")
                    with method(*args, **kwargs) as return_val:
                        result = return_val
                        yield result
                    self._add_response_as_metadata(
                        method_name=method_name,
                        data=result,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from '{method_name}' method")
                    self._add_full_exception_as_metadata(
                        method_name=method_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )
                    raise

        return decorate

    def _decorate_sync_function(
        self,
        method: AnyCallableT,
        capture_response: Optional[Union[bool, str]] = None,
        capture_error: Optional[Union[bool, str]] = None,
        method_name: Optional[str] = None,
    ) -> AnyCallableT:
        @functools.wraps(method)
        def decorate(*args, **kwargs):
            with self.provider.in_subsegment(name=f"## {method_name}") as subsegment:
                try:
                    logger.debug(f"Calling method: {method_name}")
                    response = method(*args, **kwargs)
                    self._add_response_as_metadata(
                        method_name=method_name,
                        data=response,
                        subsegment=subsegment,
                        capture_response=capture_response,
                    )
                except Exception as err:
                    logger.exception(f"Exception received from '{method_name}' method")
                    self._add_full_exception_as_metadata(
                        method_name=method_name,
                        error=err,
                        subsegment=subsegment,
                        capture_error=capture_error,
                    )
                    raise

                return response

        return cast(AnyCallableT, decorate)

    def _add_response_as_metadata(
        self,
        method_name: Optional[str] = None,
        data: Optional[Any] = None,
        subsegment: Optional[BaseSegment] = None,
        capture_response: Optional[Union[bool, str]] = None,
    ):
        """Add response as metadata for given subsegment

        Parameters
        ----------
        method_name : str, optional
            method name to add as metadata key, by default None
        data : Any, optional
            data to add as subsegment metadata, by default None
        subsegment : BaseSegment, optional
            existing subsegment to add metadata on, by default None
        capture_response : bool, optional
            Do not include response as metadata
        """
        if data is None or not capture_response or subsegment is None:
            return

        subsegment.put_metadata(key=f"{method_name} response", value=data, namespace=self.service)

    def _add_full_exception_as_metadata(
        self,
        method_name: str,
        error: Exception,
        subsegment: BaseSegment,
        capture_error: Optional[bool] = None,
    ):
        """Add full exception object as metadata for given subsegment

        Parameters
        ----------
        method_name : str
            method name to add as metadata key, by default None
        error : Exception
            error to add as subsegment metadata, by default None
        subsegment : BaseSegment
            existing subsegment to add metadata on, by default None
        capture_error : bool, optional
            Do not include error as metadata, by default True
        """
        if not capture_error:
            return

        subsegment.put_metadata(key=f"{method_name} error", value=error, namespace=self.service)

    @staticmethod
    def _disable_tracer_provider():
        """Forcefully disables tracing"""
        logger.debug("Disabling tracer provider...")
        aws_xray_sdk.global_sdk_config.set_sdk_enabled(False)

    @staticmethod
    def _is_tracer_disabled() -> Union[bool, str]:
        """Detects whether trace has been disabled

        Tracing is automatically disabled in the following conditions:

        1. Explicitly disabled via `TRACE_DISABLED` environment variable
        2. Running in Lambda Emulators, or locally where X-Ray Daemon will not be listening
        3. Explicitly disabled via constructor e.g `Tracer(disabled=True)`

        Returns
        -------
        Union[bool, str]
        """
        logger.debug("Verifying whether Tracing has been disabled")
        is_lambda_env = os.getenv(constants.LAMBDA_TASK_ROOT_ENV)
        is_disabled = resolve_truthy_env_var_choice(env=os.getenv(constants.TRACER_DISABLED_ENV, "false"))

        if is_disabled:
            logger.debug("Tracing has been disabled via env var POWERTOOLS_TRACE_DISABLED")
            return is_disabled

        if not is_lambda_env:
            logger.debug("Running outside Lambda env; disabling Tracing")
            return True

        return False

    def __build_config(
        self,
        service: Optional[str] = None,
        disabled: Optional[bool] = None,
        auto_patch: Optional[bool] = None,
        patch_modules: Optional[Sequence[str]] = None,
        provider: Optional[BaseProvider] = None,
    ):
        """Populates Tracer config for new and existing initializations"""
        is_disabled = disabled if disabled is not None else self._is_tracer_disabled()
        is_service = resolve_env_var_choice(choice=service, env=os.getenv(constants.SERVICE_NAME_ENV))

        # Logic: Choose overridden option first, previously cached config, or default if available
        self._config["provider"] = provider or self._config["provider"] or self._patch_xray_provider()
        self._config["auto_patch"] = auto_patch if auto_patch is not None else self._config["auto_patch"]
        self._config["service"] = is_service or self._config["service"]
        self._config["disabled"] = is_disabled or self._config["disabled"]
        self._config["patch_modules"] = patch_modules or self._config["patch_modules"]

    @classmethod
    def _reset_config(cls):
        cls._config = copy.copy(cls._default_config)

    def _patch_xray_provider(self):
        # Due to Lazy Import, we need to activate `core` attrib via import
        # we also need to include `patch`, `patch_all` methods
        # to ensure patch calls are done via the provider
        from aws_xray_sdk.core import xray_recorder  # type: ignore

        provider = xray_recorder
        provider.patch = aws_xray_sdk.core.patch
        provider.patch_all = aws_xray_sdk.core.patch_all

        return provider

    def _disable_xray_trace_batching(self):
        """Configure X-Ray SDK to send subsegment individually over batching
        Known issue: https://github.com/aws-powertools/powertools-lambda-python/issues/283
        """
        if self.disabled:
            logger.debug("Tracing has been disabled, aborting streaming override")
            return

        aws_xray_sdk.core.xray_recorder.configure(streaming_threshold=0)

    def _is_xray_provider(self):
        return "aws_xray_sdk" in self.provider.__module__

    def ignore_endpoint(self, hostname: Optional[str] = None, urls: Optional[List[str]] = None):
        """If you want to ignore certain httplib requests you can do so based on the hostname or URL that is being
        requested.

        > NOTE: If the provider is not xray, nothing will be added to ignore list

        Documentation
        --------------
        - https://github.com/aws/aws-xray-sdk-python#ignoring-httplib-requests

        Parameters
        ----------
        hostname : Optional, str
            The hostname is matched using the Python fnmatch library which does Unix glob style matching.
        urls: Optional, List[str]
            List of urls to ignore. Example `tracer.ignore_endpoint(urls=["/ignored-url"])`
        """
        if not self._is_xray_provider():
            return

        from aws_xray_sdk.ext.httplib import add_ignored  # type: ignore

        add_ignored(hostname=hostname, urls=urls)
