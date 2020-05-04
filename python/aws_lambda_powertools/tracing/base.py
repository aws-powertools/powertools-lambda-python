from __future__ import annotations

import abc
import copy
import functools
import logging
import os
from typing import Any, Callable, List

import aws_xray_sdk
import aws_xray_sdk.core

is_cold_start = True
logger = logging.getLogger(__name__)


class TracerProvider(metaclass=abc.ABCMeta):
    """Tracer provider abstract class

    Providers should be initialized independently. This
    allows providers to control their config/initialization,
    and only pass a class instance to
    ```aws_lambda_powertools.tracing.tracer.Tracer```.

    Trace providers should implement the following methods:

    * **patch**
    * **create_subsegment**
    * **end_subsegment**
    * **put_metadata**
    * **put_annotation**
    * **disable_tracing_provider**

    These methods will be called by
    ```aws_lambda_powertools.tracing.tracer.Tracer```.
    See ```aws_lambda_powertools.tracing.base.XrayProvider```
    for a reference implementation.

    Example
    -------
    **Client using a custom tracing provider**

        from aws_lambda_powertools.tracing import Tracer
        ... import ... ProviderX
        custom_provider = ProviderX()
        tracer = Tracer(service="greeting", provider=custom_provider)
    """

    @abc.abstractmethod
    def patch(self, modules: List[str] = None):
        """Patch modules for instrumentation

        If modules are None, it should patch
        all supported modules by the provider.

        Parameters
        ----------
        modules : List[str], optional
            List of modules to be pathced, by default None
            e.g. `['boto3', 'requests']`
        """
        raise NotImplementedError

    @abc.abstractmethod
    def create_subsegment(self, name: str):
        """Creates subsegment/span with a given name

        Parameters
        ----------
        name : str
            Subsegment/span name
        """
        raise NotImplementedError

    @abc.abstractmethod
    def end_subsegment(self):
        """Ends an existing subsegment"""
        raise NotImplementedError

    @abc.abstractmethod
    def put_metadata(self, key: str, value: Any, namespace: str = None):
        """Adds metadata to existing segment/span or subsegment

        Parameters
        ----------
        key : str
            Metadata key
        value : Any
            Metadata value
        namespace : str, optional
            Metadata namespace, by default None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def put_annotation(self, key: str, value: Any):
        """Adds annotation/label to existing segment/span or subsegment

        Parameters
        ----------
        key : str
            Annotation/label key
        value : Any
            Annotation/label value
        """
        raise NotImplementedError

    @abc.abstractmethod
    def disable_tracing_provider(self):
        """Forcefully disables tracing provider"""
        raise NotImplementedError


class XrayProvider(TracerProvider):
    def __init__(self, client: aws_xray_sdk.core.xray_recorder = aws_xray_sdk.core.xray_recorder):
        self.client = client

    def create_subsegment(self, name: str) -> aws_xray_sdk.core.models.subsegment:
        """Creates subsegment/span with a given name

        Parameters
        ----------
        name : str
            Subsegment name

        Example
        -------

        **Creates a subsegment**

            self.create_subsegment(name="a meaningful name")

        Returns
        -------
        aws_xray_sdk.core.models.subsegment
            AWS X-Ray Subsegment
        """
        # Will no longer be needed once #155 is resolved
        # https://github.com/aws/aws-xray-sdk-python/issues/155
        subsegment = self.client.begin_subsegment(name=name)
        global is_cold_start
        if is_cold_start:
            logger.debug("Annotating cold start")
            subsegment.put_annotation(key="ColdStart", value=True)
            is_cold_start = False

        return subsegment

    def end_subsegment(self):
        """Ends an existing subsegment"""
        self.client.end_subsegment()

    def put_annotation(self, key, value):
        """Adds annotation to existing segment or subsegment

        Example
        -------
        Custom annotation for a pseudo service named payment

            tracer = Tracer(service="payment")
            tracer.put_annotation("PaymentStatus", "CONFIRMED")

        Parameters
        ----------
        key : str
            Annotation key (e.g. PaymentStatus)
        value : Any
            Value for annotation (e.g. "CONFIRMED")
        """
        self.client.put_annotation(key=key, value=value)

    def put_metadata(self, key, value, namespace=None):
        """Adds metadata to existing segment or subsegment

        Parameters
        ----------
        key : str
            Metadata key
        value : object
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
        self.client.put_metadata(key=key, value=value, namespace=namespace)

    def patch(self, modules: List[str] = None):
        """Patch modules for instrumentation.

        Patches all supported modules by default if none are given.

        Parameters
        ----------
        modules : List[str]
            List of modules to be patched, optional by default
        """
        if modules is None:
            aws_xray_sdk.core.patch_all()
        else:
            aws_xray_sdk.core.patch(modules)

    def disable_tracing_provider(self):
        """Forcefully disables X-Ray tracing globally"""
        aws_xray_sdk.global_sdk_config.set_sdk_enabled(False)
