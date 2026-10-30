<!-- markdownlint-disable MD041 MD043 -->
# 0007. Lean dependencies

Status: Accepted

## Context

Every dependency we add is installed in every customer function that uses Powertools for AWS Lambda (Python), is part of their security surface, can conflict with versions they pin themselves, and adds to cold start ([ADR 0002](0002-every-millisecond-counts.md)). The core package depends on `jmespath` and `typing-extensions` only. Everything else is optional and installed through extras.

## Decision

- No new required dependency without a maintainer decision recorded in the issue. The default answer is no; the bar is "cannot be done reasonably without it".
- Optional functionality goes behind an extra in `pyproject.toml` and is imported lazily, so customers who do not use it do not install or load it.
- Version ranges are wide: a lower bound we tested and an upper bound at the next major. Narrow pins conflict with what customers already have in their functions.
- A dependency must support every Python version we support ([ADR 0003](0003-python-versions.md)) and both architectures.
- We do not vendor code to avoid a dependency unless the alternative is worse, and we do not add a dependency for something a few lines of standard library can do.
- Dependency bumps arrive through automation and are tested across the supported matrix before release.

## Consequences

- Features sometimes take more code than a library would need. That is accepted.
- The layer stays small and never carries what the Lambda runtime already provides ([ADR 0004](0004-layer-and-packaging.md)).
- Reviews of `pyproject.toml` and `uv.lock` changes are as careful as reviews of code.

## When reviewing or writing a change

If `pyproject.toml` changes, ask three questions: is it required or optional, is it imported lazily, and does it install cleanly on the oldest and newest supported Python on both architectures.
