<!-- markdownlint-disable MD041 MD043 -->
# 0004. Layer and packaging

Status: Accepted

## Context

We have customers consuming Powertools for AWS Lambda (Python) through the public Lambda layer, built in `layer_v3/`, and customers packaging it themselves in a zip or container image. Both are first-class. The layer sits on `sys.path` ahead of the Lambda runtime's own packages, so anything we ship in it shadows what the runtime provides.

The runtime already provides `boto3`, `botocore` and their dependencies (`urllib3`, `s3transfer`, `python-dateutil`, `six`, `jmespath`). When we shipped `urllib3` by accident (see issues 8555 and 8556), customers got a version of it they did not choose and that could differ from the SDK the runtime expects.

## Decision

- The layer never ships `boto3`, `botocore` or any of their dependencies. The runtime provides them, or the customer packages the version they want. Extras that pull them in are not installed into the layer.
- The layer is built from the released package with the same build for every supported Python version and for `x86_64` and `arm64`. The two architectures must be functionally identical.
- The layer ships one compiled `.pyc` per `.py` (`compileall` with checked hashes) so cold starts do not pay for bytecode compilation.
- The layer contains Powertools for AWS Lambda (Python) and its optional extras only. A dependency we would not accept in `pyproject.toml` does not enter the layer either ([ADR 0007](0007-lean-dependencies.md)).
- The zip package built from the wheel is the reference for customers who do not use the layer; what works in the layer must work in the zip and vice versa.

## Consequences

- Before a release the layer is built per version and architecture and exercised in real functions, both as a layer and as a zip, on cold and warm starts.
- A change in `pyproject.toml` extras or dependencies is also a layer change and is reviewed as one.
- Customers who need a specific `boto3` version keep full control of it.

## When reviewing or writing a change

If a PR touches dependencies, extras or `layer_v3/`, check what ends up in `python/lib/python3.*/site-packages` of a built layer. Nothing from the runtime's own set may appear there.
