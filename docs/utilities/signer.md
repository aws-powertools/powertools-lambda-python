---
title: Request signing
description: Sign HTTP requests to AWS services with SigV4 and SigV4a
status: new
---

<!-- markdownlint-disable MD013 -->

Sign HTTP requests to IAM-protected AWS endpoints with [Signature Version 4](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv4_signing.html){target="_blank"}, using the `botocore` the Lambda runtime already ships. Part of the Auth utility, next to [JWT verification](auth.md) and the [OAuth2 client](oauth2.md).

## Key features

* Sign a request and get back the headers and URL to send, with any HTTP client
* Drop-in `auth=` objects for `requests` and `httpx` that sign every call
* Region and credentials read from the Lambda environment, no credential provider chain on the cold start path
* S3 canonical rules applied when the service is S3
* SigV4a for multi-region endpoints such as S3 Multi-Region Access Points, behind an optional extra

## Getting started

### Install

Nothing to install for SigV4: the signer only needs `botocore`, which the Lambda runtime provides. If you package your function without the runtime's `boto3`, add `aws-lambda-powertools[aws-sdk]`.

SigV4a needs the `awscrt` package, which the runtime does not ship:

```bash
pip install "aws-lambda-powertools[auth-sigv4a]"
```

### Sign requests with `requests`

Pass `requests_auth()` as `auth=` and every request through that session is signed on the way out. The example calls an API Gateway REST API with IAM authorization; the signing name for API Gateway is `execute-api`.

=== "requests_client.py"

    ```python hl_lines="5 11 13 17"
    --8<-- "examples/auth/signer/src/requests_client.py"
    ```

### Sign requests with `httpx`

`httpx_auth()` does the same for `httpx`. This example calls a Lambda Function URL with `AWS_IAM` auth; the signing name is `lambda`.

=== "httpx_client.py"

    ```python hl_lines="5 10 11"
    --8<-- "examples/auth/signer/src/httpx_client.py"
    ```

### Sign only, send with any client

`sign()` never touches the network. It returns a `SignedRequest` with the `method`, the `url` to send, the `headers` including `Authorization`, and the `body`. Use them with `urllib3`, a generated client, or anything else.

=== "sign_only.py"

    ```python hl_lines="6 11 19 20"
    --8<-- "examples/auth/signer/src/sign_only.py"
    ```

!!! info "Send the URL you get back"
    The query string is re-encoded the way SigV4 canonicalises it (a space becomes `%20`, repeated keys are kept). Send `signed.url`, not the URL you passed in, or the signature will not match. The `requests` and `httpx` helpers do this for you.

### Signing names

The `service` parameter is the signing name of the target, not the hostname. Common ones:

| Target | `service` |
| --- | --- |
| API Gateway REST and HTTP APIs | `execute-api` |
| Lambda Function URLs | `lambda` |
| AppSync | `appsync` |
| OpenSearch | `es` |
| Amazon S3 | `s3` |

## Advanced

### Amazon S3

Use `service="s3"`. The signer switches to the S3 canonical URI rules, so object keys with spaces, `+` or other characters that S3 encodes differently from the rest of AWS sign correctly, and the `x-amz-content-sha256` header is added.

=== "s3_object.py"

    ```python hl_lines="10 14 15"
    --8<-- "examples/auth/signer/src/s3_object.py"
    ```

### Credentials and region outside Lambda

Inside Lambda, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN` are always set and the signer reads them. Elsewhere, pass `region=` and either `credentials=` (a `botocore.credentials.Credentials`) or `session=` (a `botocore.session.Session`, resolved through its provider chain). An explicit `credentials=` also serves cross-account calls with assumed-role credentials.

=== "outside_lambda.py"

    ```python hl_lines="7 8 9 10 11"
    --8<-- "examples/auth/signer/src/outside_lambda.py"
    ```

### SigV4a for multi-region endpoints

`SigV4aSigner` produces an ECDSA signature valid across a set of regions, which S3 Multi-Region Access Points require. Pass the regions in `region_set`, or `"*"` for every region. It needs the `auth-sigv4a` extra.

=== "sigv4a.py"

    ```python hl_lines="5 11 16"
    --8<-- "examples/auth/signer/src/sigv4a.py"
    ```

### Errors

| Exception | When |
| --- | --- |
| `SignerConfigError` | At construction: no region, no credentials, an empty `service`, or `SigV4aSigner` without `awscrt`. The message says which, and never includes credential material. |
| `TypeError` | A streaming request body was passed to a client helper. Read it into `bytes` first; SigV4 hashes the whole payload. |

A rejected signature comes back from the service as HTTP 403 with `The request signature we calculated does not match`. The usual causes are a wrong `service` name, a wrong `region`, or a client that changed the request after signing.

## Testing your code

Sign against fixed environment variables and assert on the headers that leave; the signature algorithm itself is botocore's and does not need testing on your side.

=== "test_requests_client.py"

    ```python hl_lines="7 8 9 27 28"
    --8<-- "examples/auth/signer/tests/test_requests_client.py"
    ```
