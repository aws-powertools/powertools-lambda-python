"""
AWS AppConfig configuration retrieval through the AWS AppConfig Agent Lambda extension
"""

from __future__ import annotations

import os
from http.client import HTTPConnection, HTTPException
from urllib.parse import quote, urlencode

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import resolve_env_var_choice
from aws_lambda_powertools.utilities.parameters.base import BaseProvider
from aws_lambda_powertools.utilities.parameters.exceptions import GetParameterError

DEFAULT_EXTENSION_PORT = 2772
DEFAULT_EXTENSION_TIMEOUT_SECS = 3.0


class AppConfigExtensionProvider(BaseProvider):
    """
    AWS AppConfig provider backed by the AWS AppConfig Agent Lambda extension.

    The extension runs as a Lambda layer, keeps a local cache of configuration data, polls
    AWS AppConfig in the background, and serves configuration over HTTP on localhost. This
    provider reads from that local endpoint instead of calling the AppConfig APIs with boto3.

    Parameters
    ----------
    environment: str
        Environment of the configuration
    application: str, optional
        Application of the configuration, by default POWERTOOLS_SERVICE_NAME
    port: int, optional
        Port of the extension's local HTTP server, by default AWS_APPCONFIG_EXTENSION_HTTP_PORT or 2772
    timeout: float, optional
        Seconds to wait for a response from the extension, by default 3

    Example
    -------
    **Retrieves a configuration from the AppConfig Agent Lambda extension**

        >>> from aws_lambda_powertools.utilities import parameters
        >>>
        >>> appconf_provider = parameters.AppConfigExtensionProvider(environment="my_env", application="my_app")
        >>>
        >>> value: dict = appconf_provider.get("my_conf", transform="json")

    **Retrieves selected feature flags only**

        >>> value: dict = appconf_provider.get("my_flags", transform="json", flag=["beta_ui", "new_checkout"])

    Notes
    -----
    Attach the ``AWS-AppConfig-Extension`` layer to the function and grant the execution role
    ``appconfig:StartConfigurationSession`` and ``appconfig:GetLatestConfiguration``. The extension
    uses those permissions; this provider only talks to localhost.
    """

    def __init__(
        self,
        environment: str,
        application: str | None = None,
        port: int | None = None,
        timeout: float = DEFAULT_EXTENSION_TIMEOUT_SECS,
    ):
        super().__init__()
        self.environment = environment
        self.application = resolve_env_var_choice(
            choice=application,
            env=os.getenv(constants.SERVICE_NAME_ENV, "service_undefined"),
        )
        self.port = (
            port if port is not None else int(os.getenv(constants.APPCONFIG_EXTENSION_PORT_ENV, DEFAULT_EXTENSION_PORT))
        )
        self.timeout = timeout

    def _get(self, name: str, **sdk_options) -> bytes:
        """
        Retrieve a configuration from the AppConfig Agent Lambda extension.

        Parameters
        ----------
        name: str
            Name of the configuration profile
        sdk_options: dict, optional
            Query string parameters forwarded to the extension, for example ``flag="my_flag"``
            or ``flag=["flag_a", "flag_b"]`` to retrieve selected feature flags
        """
        path = self._build_path(name=name, **sdk_options)
        connection = HTTPConnection(host="localhost", port=self.port, timeout=self.timeout)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            body = response.read()
        except (OSError, HTTPException) as exc:
            raise GetParameterError(
                f"Unable to reach the AWS AppConfig Agent Lambda extension on localhost:{self.port}. "
                "Make sure the AWS-AppConfig-Extension layer is attached to the function. "
                f"Error: {exc}",
            ) from exc
        finally:
            connection.close()

        if response.status != 200:
            raise GetParameterError(
                f"AWS AppConfig Agent Lambda extension returned HTTP {response.status} for {path}: "
                f"{body.decode('utf-8', errors='replace')}",
            )

        return body

    def _build_path(self, name: str, **sdk_options) -> str:
        path = (
            f"/applications/{quote(self.application, safe='')}"
            f"/environments/{quote(self.environment, safe='')}"
            f"/configurations/{quote(name, safe='')}"
        )
        if sdk_options:
            path = f"{path}?{urlencode(sdk_options, doseq=True)}"
        return path

    def _get_multiple(self, path: str, **sdk_options) -> dict[str, str]:
        """
        Retrieving multiple configurations is not supported by the AppConfig Agent Lambda extension
        """
        raise NotImplementedError()
