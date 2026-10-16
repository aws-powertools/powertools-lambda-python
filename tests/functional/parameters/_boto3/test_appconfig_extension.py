from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.feature_flags import AppConfigExtensionStore, AppConfigStore, FeatureFlags
from aws_lambda_powertools.utilities.parameters import AppConfigExtensionProvider, GetParameterError


class FakeExtension:
    """Minimal stand-in for the AWS AppConfig Agent local HTTP endpoint."""

    def __init__(self):
        self.requests: list[tuple[str, dict]] = []
        self.responses: dict[str, tuple[int, bytes]] = {}
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                parts = urlsplit(self.path)
                fake.requests.append((parts.path, parse_qs(parts.query)))
                status, body = fake.responses.get(parts.path, (404, b'{"message":"not found"}'))
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):  # keep test output quiet
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def respond(self, path: str, body: dict | bytes, status: int = 200):
        self.responses[path] = (status, body if isinstance(body, bytes) else json.dumps(body).encode())

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def extension():
    fake = FakeExtension()
    yield fake
    fake.stop()


@pytest.fixture
def config_path():
    return "/applications/my_app/environments/dev/configurations/features"


def test_get_returns_raw_bytes(extension, config_path):
    extension.respond(config_path, {"beta": True})
    provider = AppConfigExtensionProvider(environment="dev", application="my_app", port=extension.port)

    value = provider.get("features")

    assert value == b'{"beta": true}'
    assert extension.requests == [(config_path, {})]


def test_get_with_json_transform(extension, config_path):
    extension.respond(config_path, {"beta": True, "limit": 3})
    provider = AppConfigExtensionProvider(environment="dev", application="my_app", port=extension.port)

    assert provider.get("features", transform="json") == {"beta": True, "limit": 3}


def test_sdk_options_become_query_string(extension, config_path):
    extension.respond(config_path, {"beta": {"enabled": True}})
    provider = AppConfigExtensionProvider(environment="dev", application="my_app", port=extension.port)

    provider.get("features", transform="json", flag=["beta", "gamma"])
    provider.get("features", transform="json", flag="beta", force_fetch=True)

    assert extension.requests[0] == (config_path, {"flag": ["beta", "gamma"]})
    assert extension.requests[1] == (config_path, {"flag": ["beta"]})


def test_identifiers_are_url_encoded(extension):
    path = "/applications/my%20app/environments/dev%2Ftest/configurations/my%20features"
    extension.respond(path, {"ok": True})
    provider = AppConfigExtensionProvider(environment="dev/test", application="my app", port=extension.port)

    assert provider.get("my features", transform="json") == {"ok": True}
    assert extension.requests == [(path, {})]


def test_values_are_cached_until_max_age(extension, config_path):
    extension.respond(config_path, {"beta": True})
    provider = AppConfigExtensionProvider(environment="dev", application="my_app", port=extension.port)

    provider.get("features", max_age=60)
    provider.get("features", max_age=60)
    provider.get("features", max_age=60, force_fetch=True)

    assert len(extension.requests) == 2


def test_non_200_raises_get_parameter_error_with_details(extension, config_path):
    extension.respond(config_path, b'{"message":"configuration not found"}', status=404)
    provider = AppConfigExtensionProvider(environment="dev", application="my_app", port=extension.port)

    with pytest.raises(GetParameterError, match="HTTP 404.*configuration not found"):
        provider.get("features")


def test_unreachable_extension_mentions_the_layer():
    with socket.socket() as sock:  # grab a port nothing listens on
        sock.bind(("127.0.0.1", 0))
        free_port = sock.getsockname()[1]
    provider = AppConfigExtensionProvider(environment="dev", application="my_app", port=free_port, timeout=1)

    with pytest.raises(GetParameterError, match="AWS-AppConfig-Extension layer"):
        provider.get("features")


def test_port_defaults_to_extension_env_var_and_explicit_port_wins(monkeypatch):
    monkeypatch.setenv("AWS_APPCONFIG_EXTENSION_HTTP_PORT", "3000")

    assert AppConfigExtensionProvider(environment="dev", application="my_app").port == 3000
    assert AppConfigExtensionProvider(environment="dev", application="my_app", port=4000).port == 4000

    monkeypatch.delenv("AWS_APPCONFIG_EXTENSION_HTTP_PORT")
    assert AppConfigExtensionProvider(environment="dev", application="my_app").port == 2772


def test_application_defaults_to_service_name(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", "orders")

    assert AppConfigExtensionProvider(environment="dev").application == "orders"


def test_get_multiple_is_not_supported(extension):
    provider = AppConfigExtensionProvider(environment="dev", application="my_app", port=extension.port)

    # BaseProvider wraps provider errors, so the unsupported operation surfaces as GetParameterError
    with pytest.raises(GetParameterError):
        provider.get_multiple("/features")


def test_provider_is_exported_from_parameters():
    assert parameters.AppConfigExtensionProvider is AppConfigExtensionProvider


def test_feature_flags_store_uses_extension(extension, config_path, monkeypatch):
    monkeypatch.setenv("AWS_APPCONFIG_EXTENSION_HTTP_PORT", str(extension.port))
    extension.respond(
        config_path,
        {
            "beta": {
                "default": False,
                "rules": {
                    "tenant is acme": {
                        "when_match": True,
                        "conditions": [{"action": "EQUALS", "key": "tenant", "value": "acme"}],
                    },
                },
            },
        },
    )
    store = AppConfigStore(environment="dev", application="my_app", name="features", use_extension=True)
    flags = FeatureFlags(store=store)

    assert isinstance(store._conf_store, AppConfigExtensionProvider)
    assert flags.evaluate(name="beta", context={"tenant": "acme"}, default=False) is True
    assert flags.evaluate(name="beta", context={"tenant": "other"}, default=False) is False
    assert extension.requests[0][0] == config_path


def test_feature_flags_extension_store_is_a_preconfigured_appconfig_store(extension, config_path, monkeypatch):
    monkeypatch.setenv("AWS_APPCONFIG_EXTENSION_HTTP_PORT", str(extension.port))
    extension.respond(config_path, {"beta": {"default": True}})
    store = AppConfigExtensionStore(environment="dev", application="my_app", name="features", max_age=0)

    assert isinstance(store, AppConfigStore)
    assert isinstance(store._conf_store, AppConfigExtensionProvider)
    assert FeatureFlags(store=store).evaluate(name="beta", context={}, default=False) is True
