<!-- markdownlint-disable MD041 MD043 -->
# 0002. Every millisecond counts

Status: Accepted

## Context

Powertools for AWS Lambda (Python) is imported at the top of most handlers that use it, so our import time is part of every cold start of every customer. A dependency pulled in at import, a schema compiled at module load or a client created eagerly costs milliseconds on each cold start for everyone, including customers who never use that feature.

We measure this. `tests/performance/` has import-time and initialisation tests with hard limits, and they fail the build when crossed. The layer ships compiled bytecode for the same reason ([ADR 0004](0004-layer-and-packaging.md)).

## Decision

Startup cost is a feature we protect.

- Importing `aws_lambda_powertools` and any single utility must stay within the limits in `tests/performance/`. A change that moves a limit has to justify it in the PR, and the justification is the exception, not the norm.
- Optional and heavy dependencies (`pydantic`, `aws-xray-sdk`, `fastjsonschema`, `redis`, `boto3` itself) are imported only by the utility that uses them, never by the package root or by a shared module. A customer who imports the Logger must not pay for `pydantic`; a customer who imports the Parser must not pay for `aws-xray-sdk`.
- Nothing runs at import time beyond defining names. No network calls, no client creation, no file reads, no schema compilation. Work happens on first use.
- New code paths in the hot path of an invocation (per record, per request) are reviewed for allocations and repeated work the same way.

## Consequences

- Some code is less tidy than it could be: imports inside functions, `TYPE_CHECKING` blocks for type-only imports, lazy loaders for optional modules. That is intentional.
- Adding a dependency is a performance decision as much as a maintenance one ([ADR 0007](0007-lean-dependencies.md)).
- Performance tests can flake on shared CI runners. We re-run them; we do not raise the limits to make them pass.

## When reviewing or writing a change

Look at the top of every touched module. If a new import is not from the standard library or from `aws_lambda_powertools` core, ask why it is not lazy. Run `tests/performance/` locally when you touch import paths.
