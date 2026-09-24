---
title: OAuth2 client (alpha)
description: Acquire and cache client-credentials tokens for downstream APIs
status: new
---

!!! warning "Alpha / experimental"
    This utility ships under the `auth_alpha` namespace while we collect feedback. Its public API may change before GA. Pin your Powertools version before using it in production.

`OAuth2Client` obtains bearer tokens for a Lambda function calling an OAuth2-protected API. Each client owns its resource configuration and token cache. It supports the client-credentials grant with `client_secret_basic` authentication.

Use [JWT verification](auth.md) to authenticate incoming requests. The OAuth client obtains separate credentials for outgoing requests; it does not forward an incoming caller's token.

## Key features

* Cache access tokens across warm Lambda invocations and reacquire them before expiration.
* Coordinate concurrent token requests within one client.
* Resolve a client secret for each exchange attempt.
* Select a downstream API using a provider-specific audience or an RFC 8707 resource indicator.
* Obtain headers for your HTTP client or send a synchronous authenticated request.
* Report fixed failure reasons without exposing credentials or provider responses.

## Getting started

### Install

```shell
pip install "aws-lambda-powertools[oauth2]"
```

The `oauth2` extra installs urllib3. It does not require PyJWT or cryptography. The client is available from both `aws_lambda_powertools.utilities.auth_alpha` and `aws_lambda_powertools.utilities.auth_alpha.oauth2`.

### Call a downstream API

Create the client outside the Lambda handler so warm invocations reuse its token cache. This complete Lambda loads its client secret through Parameters and calls an inventory API:

```python title="client_credentials.py"
--8<-- "examples/auth_alpha/oauth2/src/client_credentials.py"
```

Configure `TOKEN_URL`, `CLIENT_ID`, `CLIENT_SECRET_NAME`, and `INVENTORY_URL` as deployment settings. The secret must be a plain string. The function needs permission to retrieve that secret and outbound HTTPS connectivity to both endpoints. Token exchange itself requires no additional IAM permissions.

`OAuth2Client` provides two operations:

| Method | Use when |
| ------ | -------- |
| `auth_headers()` | You want an Authorization header for an application-owned HTTP client |
| `request(method, url, ...)` | You want the utility to send an authenticated HTTPS request |

Both methods acquire a token only when one is needed. Construction performs no network requests.

### Choose the resource

| Parameter | Token-request field | Purpose |
| --------- | ------------------- | ------- |
| `audience` | `audience=<value>` | Provider-specific API selection, such as an Auth0 API identifier |
| `resource` | `resource=<value>` | One resource indicator for providers supporting RFC 8707 |

These parameters are mutually exclusive and are not interchangeable. Configure the parameter supported by your provider. If neither is supplied, the provider must select the intended API through its client configuration or scope conventions; scopes alone do not universally identify a resource.

`resource` must be an absolute URI without a fragment, such as `https://inventory.example.com` or `urn:example:inventory`. Query parameters and percent-encoded characters are preserved. Relative paths and malformed URI characters are rejected during construction. `audience` remains a provider-specific, nonempty string.

Use a separate client for each API. The eventual request URL does not change the token's audience, and clients do not share token caches. Changing the requested resource requires creating a new client.

### Use your own HTTP client

`auth_headers()` returns a new dictionary containing `Authorization: Bearer <token>`. You can pass it to urllib3, requests, httpx, or another HTTP client:

```python title="headers.py"
--8<-- "examples/auth_alpha/oauth2/src/headers.py"
```

The example validates that `INVENTORY_URL` uses HTTPS before obtaining any credentials or sending requests. It uses an environment-provided secret; the Parameters loader from the first example also works here. With your own HTTP client, enforce HTTPS and configure its timeouts, redirects, and retries yourself. Never log the returned headers or forward them to an untrusted destination.

## Advanced

### Token lifetimes and concurrency

Tokens are cached while more than 30 seconds of their positive `expires_in` remain. On demand, the client reacquires a token when 30 seconds or less remain. This performs a new client-credentials exchange; it does not use an OAuth refresh token.

Tokens with an advertised lifetime of 30 seconds or less, or without `expires_in`, are returned without caching. A call does not loop trying to obtain a longer-lived token. Invalid lifetimes and tokens that expire during acquisition are rejected.
Lifetime accounting uses a monotonic clock starting immediately before the token request, after secret lookup. Secret lookup consumes the acquisition budget but does not shorten the newly issued token's lifetime.

Concurrent callers share one in-progress exchange, including short-lived tokens and failures. A waiting caller has its own acquisition deadline. Separate clients and Lambda execution environments have separate caches.

### Secret rotation and client authentication

`client_secret` accepts a nonempty string or a callable returning one. A callable runs for each exchange attempt, including retries. The client does not cache the callable's returned secret separately.

An already cached access token can remain usable after a secret changes. Parameters also has its own cache: the first example's `max_age=300` can delay observation of a changed secret by five minutes. Configure secret-provider timeouts independently; the client cannot interrupt an application-supplied callable.

The token endpoint receives form-encoded client identifiers and secrets through HTTP Basic authentication. They are not included in the form body. Providers requiring `client_secret_post`, private-key JWT, mTLS, or interactive grants need a different client.

### Timeouts, retries, and destination safety

`timeout_seconds`, defaulting to three seconds, is the token-acquisition budget, including waiting, secret lookup, token requests, and retry backoff. Configure the Lambda timeout to leave time for token acquisition, the downstream request, and your error handling.

Transport failures, HTTP 429, and HTTP 5xx responses allow at most two retries within the acquisition budget. Backoff starts at 100 milliseconds, then 200 milliseconds. Other HTTP failures, malformed token responses, and secret-loader failures are not retried.

`request()` uses a separate `timeout`, defaulting to five seconds, for connecting to the downstream API and buffering its response. It returns an urllib3 HTTP response with `.status`, `.headers`, `.data`, and `.json()`. Non-success HTTP responses are returned for your application to interpret.

The remaining budget is enforced while reading response headers and bodies, including chunked response framing.
This is not a universal wall-clock limit: synchronous DNS resolution, application-provided secret loaders, and upload producers cannot be interrupted. Their elapsed time still consumes the budget. Configure their timeouts separately where supported, and leave room in the Lambda invocation timeout.

The helper requires HTTPS, rejects an existing Authorization header, and never follows redirects or automatically retries downstream requests. It forwards only `body`, `fields`, `json`, `encode_multipart`, and `multipart_boundary` options to urllib3. Use `auth_headers()` with your own client for streaming responses or other transport options.

Header names must use HTTP token syntax: letters, digits, and the permitted token punctuation. Empty names, whitespace (including trailing spaces or tabs), and delimiters such as colons are rejected before token acquisition. Authorization is rejected regardless of casing.

!!! warning "Use trusted destination URLs"
    `request()` does not derive or restrict destinations from the configured audience or resource. Supply trusted URLs from application configuration; never pass a caller-controlled destination. A token intended for one API must not be sent to another.

### Errors and diagnostics

OAuth errors inherit from the common `AuthError` in `auth_alpha.exceptions`. Existing JWT exception imports continue to work.

| Exception | Reason | Retryable |
| --------- | ------ | --------- |
| `TokenExchangeError` | `token_exchange_failed` | True for transient endpoint failures or acquisition timeouts; otherwise false |
| `DownstreamRequestError` | `downstream_request_failed` | False: the server may already have performed the operation |

Use the fixed `reason.value` and `retryable` fields for logs and metrics:

```python title="diagnostics.py"
--8<-- "examples/auth_alpha/oauth2/src/diagnostics.py"
```

The utility performs no automatic logging. It removes provider exception chains before exposing an auth error. Never log client secrets, access tokens, Authorization headers, or full provider responses.

### Calling downstream APIs from an MCP tool

An MCP server can use the same client after authorizing the incoming caller. Obtain a separate token for the downstream API instead of forwarding the caller's bearer token. In an async tool, offload this synchronous client to a worker thread:

```python
import asyncio
from urllib.parse import quote

from mcp.server.auth.middleware.auth_context import get_access_token

# inventory_api is the configured OAuth2Client from client_credentials.py.
async def check_stock(sku: str) -> dict:
    caller = get_access_token()
    if caller is None or "inventory:read" not in caller.scopes:
        raise PermissionError("Inventory read permission is required")
    response = await asyncio.to_thread(
        inventory_api.request,
        "GET",
        f"{INVENTORY_URL}/stock/{quote(sku, safe='')}",
        timeout=5,
    )
    if response.status != 200:
        raise RuntimeError("Inventory lookup failed")
    return response.json()
```

The MCP SDK owns transport authentication and protocol error responses; adapt the permission error to your SDK's handling. Cancelling the awaiting task does not stop an in-progress worker thread, so network timeouts still apply. No MCP dependency is added to Powertools.

## Testing your code

Mock the client operation when testing application behavior, and test your provider configuration separately:

```python title="test_client_credentials.py"
--8<-- "examples/auth_alpha/oauth2/tests/test_client_credentials.py"
```
