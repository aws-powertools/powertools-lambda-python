"""A local TLS endpoint exercising the production transport without HTTP mocks."""

import ipaddress
import json
import ssl
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


@dataclass
class Reply:
    body: bytes
    status: int = 200
    headers: dict = field(default_factory=dict)
    interval: float = 0
    stall: bool = False


class LocalHTTPS:
    def __init__(self):
        self.routes = {}
        self.requests = []
        self.stop = threading.Event()
        self.url = ""

    def serve(self, path, payload, *, status=200, headers=None, interval=0, stall=False):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.routes[path] = Reply(body, status, headers or {}, interval, stall)


@pytest.fixture(scope="session")
def tls_files(tmp_path_factory):
    directory = tmp_path_factory.mktemp("auth-tls")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Powertools local test CA")])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    certificate_path = directory / "certificate.pem"
    key_path = directory / "key.pem"
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
    )
    return certificate_path, key_path


@pytest.fixture
def https_server(tls_files, monkeypatch):
    endpoint = LocalHTTPS()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):  # noqa: N802
            self.respond()

        def do_POST(self):  # noqa: N802
            self.respond()

        def respond(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            endpoint.requests.append((self.command, self.path, dict(self.headers), body))
            reply = endpoint.routes.get(self.path, Reply(b"{}", status=404))
            self.send_response(reply.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(reply.body)))
            self.send_header("Connection", "close")
            for name, value in reply.headers.items():
                self.send_header(name, value)
            self.end_headers()
            try:
                if reply.stall:
                    endpoint.stop.wait(5)
                elif reply.interval:
                    for value in reply.body:
                        if endpoint.stop.wait(reply.interval):
                            break
                        self.wfile.write(bytes([value]))
                        self.wfile.flush()
                else:
                    self.wfile.write(reply.body)
            except (OSError, ssl.SSLError):
                # Timeout and oversized-body tests deliberately close early.
                pass
            finally:
                self.close_connection = True

        def log_message(self, format, *args):  # noqa: A002
            pass

    certificate_path, key_path = tls_files
    monkeypatch.setenv("SSL_CERT_FILE", str(certificate_path))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificate_path, key_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    endpoint.url = f"https://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    try:
        yield endpoint
    finally:
        endpoint.stop.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()
