---
title: Auth
description: JWT access-token verification and OAuth client credentials for Lambda
---

Auth verifies incoming JWT access tokens and obtains separate OAuth bearer tokens for downstream APIs.
Use it inside a Lambda function or a Lambda authorizer. Prefer an API Gateway managed JWT authorizer when it meets your token profile and deployment requirements.

## Key features

* Verify asymmetric signatures, exact issuer, resource audience, expiration, and additional required claims.
* Coordinate discovery and signing-key refresh across threads with bounded key freshness.
* Protect Event Handler routes and create API Gateway IAM or simple authorizer responses.
* Validate resource-bound Cognito access tokens and combine explicitly trusted issuers.
* Acquire and cache resource-specific client-credentials tokens, including rotating client secrets.
* Adapt verification to the MCP Python SDK without a Powertools dependency on MCP.

## Getting started

### Install

```shell
pip install "aws-lambda-powertools[auth]"
```

The optional `auth` extra includes PyJWT, cryptography, and urllib3. It adds no dependencies to the base installation.
Build cryptography dependencies for your Lambda Python version and architecture; see [cross-platform builds](../build_recipes/cross-platform.md).

### Protect an HTTP route

Create a verifier outside the handler so warm invocations reuse its key cache. Configure an issuer, resource audience, and explicit algorithm allowlist.
Set `ISSUER_URL` and `RESOURCE_URL` to your provider's exact issuer and this API's identifier.

```python title="middleware.py"
--8<-- "examples/auth/src/middleware.py"
```

`require()` validates the Bearer token and all requested scopes before executing the route. Verified claims are available through `app.context["claims"]`.
Claims remain available while downstream middleware and the handler execute, then are removed even if either raises an exception.
Event Handler clears context after resolving the invocation. The same middleware works with REST API, ALB, and Lambda Function URL resolvers.
Configure CORS preflight and public routes separately.

| Failure | Response | `WWW-Authenticate` |
| ------- | -------- | ------------------ |
| Missing Authorization | 401 | `Bearer` |
| Invalid token or malformed scope claim | 401 | `Bearer error="invalid_token"` |
| Missing required scope | 403 | `Bearer error="insufficient_scope", scope="orders:read"` |
| Additional authorization denied | 403 | None |
| Signing keys unavailable | 503 | None |

### Verify directly

`verify(token)` accepts the token without the `Bearer` prefix and returns a dictionary of verified claims.
It always requires `iss`, `aud`, and `exp`. `required_claims` adds requirements without replacing these baseline checks.

```python
from aws_lambda_powertools.utilities.auth import JWTVerifier

verifier = JWTVerifier(
    issuer="https://idp.example.com/",
    audience="https://orders.example.com",
    algorithms=["RS256"],
    required_claims=["sub"],
)
```

Absent an explicit `jwks_uri` or static `jwks`, discovery uses the configured issuer's `/.well-known/openid-configuration`.
Discovery must advertise that exact issuer and an HTTPS JWKS URL. URLs supplied by token headers are never used for discovery.

### Call a downstream API

Create one `OAuth2Client` per downstream resource. This example loads a client secret from Secrets Manager and requests a distinct Inventory access token.
The Lambda role needs permission to read the configured secret.

```python title="outbound.py"
--8<-- "examples/auth/src/outbound.py"
```

Use `auth_headers()` to integrate with an application-owned HTTP client. Pass only trusted destination URLs.
`request()` requires HTTPS, rejects another Authorization header, and disables redirects and downstream retries.
It returns a urllib3 response with `.status`, `.data`, and `.json()`; check the downstream status before using the body.

## Advanced

### Token profiles and scope checks

The generic profile checks signature, exact issuer, at least one configured audience, and finite numeric `exp`, `nbf`, and `iat` claims when present.
Expiration is required. The default clock allowance is 60 seconds, configurable with `clock_skew_seconds`.
Supported algorithms are RS256/384/512, PS256/384/512, ES256/384/512, ES256K, and EdDSA. HMAC and unsigned JWTs are rejected.
Keys must have a matching `kid`, compatible algorithm and key type, and signing/verification metadata when supplied.

Applications must select access tokens for their resource; the generic profile cannot infer a provider's token purpose.
Require and validate provider-specific claims when an issuer can mint other token types with the same audience.
Local JWT verification does not check individual-token revocation.

Scopes come from the first present claim in this order: `scope`, `scp`, `scopes`.
A claim can be a space-separated string or a list of strings. A malformed higher-priority claim is rejected without falling back to another claim.
All required scopes must be present.

An optional `authorize` callback receives verified claims and must return `True`:

```python
middleware = verifier.require(
    scopes=["orders:read"],
    authorize=lambda claims: claims.get("tenant") == "example",
)
```

An `on_error` callback receives an object with `status_code` and `headers` and must return an Event Handler `Response`.
Preserve those fields when customizing the body. This callback replaces the error response; it does not invoke the protected handler.

### Key freshness, rotation, and outages

| Setting | Default | Behavior |
| ------- | ------- | -------- |
| `timeout_seconds` | 3 | Budget for discovery, JWKS requests, and waiting for another refresh |
| `jwks_max_age_seconds` | 300 | Maximum age of a successfully fetched key set |
| `unknown_kid_cooldown_seconds` | 300 | Minimum interval between fetches triggered by unknown key IDs |

Compatible verifiers in one process share a key-set cache; distinct issuers or cache policies are isolated.
Concurrent misses share a refresh. Expiration requires a fresh key set even when the unknown-key cooldown has not elapsed.
A successful refresh replaces the entire set, including removal of previously trusted keys. No independent parsed-key cache retains removed keys.

A failed refresh backs off for 1, 2, 4, 8, 16, then 30 seconds. During that interval, known keys can still be used within their original maximum age.
Expired keys are never used after a failed refresh. Unknown keys during a cooldown are rejected, so a newly published key may take time to become usable.
Choose freshness and cooldown settings together with your provider's key rotation policy.

`prefetch()` fetches absent or expired keys during initialization. Later rotation, expiration, and outages can still cause network I/O.
Static `jwks` is copied when constructing the verifier and performs no discovery or refresh:

```python
import json

from aws_lambda_powertools.utilities import parameters

key_set = parameters.get_parameter("/orders/jwks", max_age=3600)
verifier = JWTVerifier(
    issuer="https://idp.internal",
    audience="https://orders.internal",
    algorithms=["ES256"],
    jwks=json.loads(key_set),
)
```

Parameters' cache lifetime does not refresh that static snapshot. Recreate the verifier or recycle its execution environment when keys change.
You own static-key rotation and removal.

### Cognito and multiple issuers

```python
cognito = JWTVerifier.cognito(
    user_pool_id="us-east-1_abc123",
    client_id="orders-client",
    audience="https://orders.example.com",
)
combined = JWTVerifier.any_of(verifier, cognito)
```

The Cognito profile requires RS256, `token_use="access"`, the configured `client_id`, and the resource `aud`.
The client must request resource binding. ID tokens and Cognito access tokens without `aud` are rejected.

`any_of()` uses the unverified issuer only to select an explicitly configured verifier, then performs all verification through it.
Unknown issuers trigger no discovery. Duplicate issuer configurations are rejected as ambiguous.
The combined verifier supports `verify()`, `prefetch()`, `require()`, and `authorize()`.

### Lambda authorizers

```python title="authorizer.py"
--8<-- "examples/auth/src/authorizer.py"
```

The helper accepts raw dictionaries or the corresponding Powertools authorizer Data Classes.

| Event | `response_format` | Result |
| ----- | ----------------- | ------ |
| REST API TOKEN or REQUEST | `iam` | Serialized IAM policy |
| HTTP API REQUEST payload 1.0 | `iam` | Serialized IAM policy |
| HTTP API REQUEST payload 2.0 | `iam` | Serialized IAM policy |
| HTTP API REQUEST payload 2.0, simple responses enabled | `simple` | Serialized `isAuthorized` response |

IAM allows require a nonempty string `sub` as principal and cover only the supplied request ARN.
Wildcard, missing, or malformed ARNs raise `ValueError`; the helper cannot construct a request-specific IAM policy without a valid ARN.
Other routes need their own decision.
Invalid tokens and insufficient scopes produce a Deny or `isAuthorized=False`; unavailable signing keys raise `JWKSFetchError`.

No claims are copied to context by default. `context_claims` copies only selected scalar values, omitting arrays, objects, and nulls.
The name `claims` is reserved in authorizer context.

#### Deployment and Gateway caching

Disable authorizer-result caching to verify each request. This SAM example sets `ReauthorizeEvery: 0` for both REST and HTTP authorizers;
the underlying API Gateway setting is `AuthorizerResultTtlInSeconds: 0`.
HTTP simple responses also require payload version 2.0 and `EnableSimpleResponses: true`.

```yaml title="template.yaml"
--8<-- "examples/auth/template.yaml"
```

If you enable result caching later, a cached decision can outlive the JWT's expiration or a signing key's removal.
The verifier's key-cache settings do not control Gateway's result cache.
HTTP simple responses can apply to multiple routes sharing an identity cache key; include `$context.routeKey` for route-specific decisions.
Route-aware keys still do not recheck an expired token. Cached IAM policies must cover exactly the routes they authorize; this helper deliberately returns one concrete resource.

### OAuth client credentials

Only `client_secret_basic` is supported. Client ID and secret are individually form-encoded before constructing HTTP Basic credentials.
They are never added to the request body. `audience` and RFC 8707 `resource` are optional, mutually exclusive request fields; choose the one your provider supports.
Scopes and resource selection are fixed per client, and separate instances never share tokens.

Tokens are cached until 30 seconds before their advertised expiration, measured conservatively from request start using a monotonic clock.
Tokens with 30 seconds or less remaining, or no `expires_in`, are returned without caching. Already elapsed lifetimes and malformed responses are rejected.
Concurrent acquisition shares one exchange, including short-lived tokens for callers already waiting on that exchange.

A secret callable is invoked on each exchange attempt. Existing access tokens remain usable until their own refresh boundary.
In the Parameters example, the provider's `max_age=300` can delay observation of a changed secret by five minutes.

`timeout_seconds` defaults to 3 for acquisition, including at most two retries with backoff for network failures, HTTP 429, and HTTP 5xx.
Other error responses and malformed successful responses are not retried. The `request(timeout=5)` budget is separate and applies to the downstream operation.
Synchronous OS name resolution and application-provided secret callables cannot be forcibly interrupted; configure secret-provider timeouts accordingly.

### MCP Python SDK adapter

The following adapter targets the `MCPServer` interface in MCP Python SDK 2.2.0 (`mcp==2.2.0`),
following the [MCP authorization tutorial](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/authorization).
Install that SDK separately. This example maps Keycloak-style `azp`, `sub`, and `scope` claims; other providers require their own mapping.

```python
import asyncio

from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl

from aws_lambda_powertools.utilities.auth import JWTVerifier
from aws_lambda_powertools.utilities.auth.exceptions import InvalidTokenError, JWKSFetchError

RESOURCE_URL = "https://mcp.example.com"
ISSUER_URL = "https://keycloak.example.com/realms/mcp"
verifier = JWTVerifier(
    issuer=ISSUER_URL,
    audience=RESOURCE_URL,
    algorithms=["RS256"],
    required_claims=["azp", "sub", "scope"],
)


class PowertoolsTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            claims = await asyncio.to_thread(verifier.verify, token)
        except (InvalidTokenError, JWKSFetchError):
            return None
        if not all(isinstance(claims[name], str) for name in ("azp", "sub", "scope")):
            return None
        if not claims["azp"] or not claims["sub"]:
            return None
        return AccessToken(
            token=token,
            client_id=claims["azp"],
            subject=claims["sub"],
            scopes=claims["scope"].split(),
            expires_at=claims["exp"],
            resource=RESOURCE_URL,
        )


mcp = MCPServer(
    name="orders",
    token_verifier=PowertoolsTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(ISSUER_URL),
        resource_server_url=AnyHttpUrl(RESOURCE_URL),
        validate_token_resource=True,
        required_scopes=["mcp:tools"],
    ),
)
```

The SDK owns transport, Protected Resource Metadata, and authentication challenges. This adapter maps both invalid tokens and unavailable keys to failed authentication.
A distinct availability response requires integration at the SDK transport boundary.
`asyncio.to_thread()` keeps synchronous key fetches off the event loop; cancelling the await does not terminate a running request.

Tools can enforce permissions using the verified SDK access token:

```python
from mcp.server.auth.middleware.auth_context import get_access_token


def require_scope(scope: str):
    caller = get_access_token()
    if caller is None or scope not in caller.scopes:
        raise PermissionError("Required tool permission is missing")
```

Use the targeted SDK's supported tool-error handling for permission failures. Raising `PermissionError` alone does not implement an HTTP challenge or a scope-upgrade flow.
For downstream calls, use a separate `OAuth2Client` and offload its synchronous operation:

```python
from urllib.parse import quote


@mcp.tool()
async def check_stock(sku: str) -> dict:
    require_scope("inventory:read")
    response = await asyncio.to_thread(
        inventory_api.request,
        "GET",
        f"https://inventory.example.com/stock/{quote(sku, safe='')}",
        timeout=5,
    )
    if response.status != 200:
        raise RuntimeError("Inventory lookup failed")
    return response.json()
```

Configure `inventory_api` as in the outbound example. Never forward the incoming MCP bearer token to another resource.
API Gateway authorizers in front of an MCP server also require deployment-specific metadata routes and discovery/challenge behavior;
an authorizer Deny response alone does not implement MCP authorization.

### Errors and diagnostics

`AuthError` is the base error. `InvalidTokenError` includes `InvalidClaimsError`, `TokenExpiredError`, and `InvalidSignatureError`.
`JWKSFetchError` is separate from invalid-token errors so applications can distinguish unavailable verification infrastructure.
`TokenExchangeError` covers unsuccessful token acquisition.

Errors have fixed credential-free messages. Public verification, prefetch, and OAuth operations detach underlying exception causes and contexts,
including errors raised by secret loaders. Utility representations omit tokens and secrets.
Do not log token dictionaries, request headers, secret-provider errors, or token-endpoint response bodies in application code.

Opaque-token introspection, delegated token exchange, interactive grants, SigV4, additional OAuth client-authentication methods, and native async clients are outside this utility.

## Testing your code

Use `mock_claims` to test route behavior without cryptography or network calls. Supply an Authorization header so the middleware still exercises credential extraction.

```python
from aws_lambda_powertools.utilities.auth.testing import mock_claims

from middleware import app, verifier


def test_orders(http_api_event, lambda_context):
    http_api_event["headers"]["authorization"] = "Bearer application-test"
    with mock_claims(verifier, {"sub": "test-user", "scope": "orders:read"}):
        response = app.resolve(http_api_event, lambda_context)
    assert response["statusCode"] == 200
```

The helper restores `verify()` on exit and returns independent copies of the supplied claims.
It deliberately bypasses signature and claim validation. Keep separate tests for real verification, key rotation, and authorization policy.
