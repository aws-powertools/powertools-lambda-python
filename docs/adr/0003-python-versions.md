<!-- markdownlint-disable MD041 MD043 -->
# 0003. Python versions follow the Lambda runtimes

Status: Accepted

## Context

Lambda adds a Python runtime shortly after each CPython release and deprecates runtimes on its own schedule. Customers move at different speeds, and a library that drops a version early strands people who cannot upgrade yet, while a library that lags blocks early adopters from using the newest runtime.

## Decision

Our supported Python versions are exactly the Python runtimes Lambda supports.

- We add a version when the Lambda runtime becomes available, and ideally test against pre-release builds so support lands on day one.
- We drop a version only after Lambda deprecates its runtime, following the Lambda runtime deprecation dates.
- The CI matrix (`quality_check`) runs the full suite on every supported version. Green on one version is not green.
- Syntax and standard-library usage are limited to the oldest supported version. Newer language features arrive when the oldest runtime that lacks them is dropped, never before.
- The Lambda layer is published for every supported version and both architectures ([ADR 0004](0004-layer-and-packaging.md)).

## Consequences

- `requires-python` in `pyproject.toml` and the CI matrix move together, in a dedicated maintenance PR, not as a side effect of a feature.
- Code that needs a newer feature carries a compatibility path or waits.
- Dependencies we accept must themselves support the whole range ([ADR 0007](0007-lean-dependencies.md)).

## When reviewing or writing a change

Check the oldest version in the matrix before using a new syntax or stdlib API. If CI only ran on the latest version locally, run at least the oldest one too.
