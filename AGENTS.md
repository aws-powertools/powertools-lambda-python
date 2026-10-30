<!-- markdownlint-disable MD041 MD043 -->
# Working on Powertools for AWS Lambda (Python)

Short guide for anyone, human or coding agent, changing this repository. It points to the sources of truth instead of repeating them. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the process and [docs/adr](docs/adr/README.md) for the premises behind the rules below.

## Before you start

- Work from an issue that a maintainer triaged. PRs on untriaged issues usually wait or get closed.
- One issue, one PR. Do not bundle unrelated fixes, even small ones.
- Branch from `develop`. Keep the diff limited to what the issue needs; do not reformat or "improve" code you did not have to touch.

## Commands

```bash
make dev                # uv sync, pre-commit hooks
make lint               # ruff format + ruff check (aws_lambda_powertools, tests, examples)
make mypy               # static typing, must pass
uv run pytest tests/unit tests/functional/<utility>      # fast loop for one utility
make test               # full unit + functional + performance, what CI runs
make pr                 # everything CI checks, run it before opening the PR
```

Do not run the full suite with `pytest -n auto`; collection differs between workers and it fails for reasons unrelated to your change.

## What a PR needs to pass

- Title follows [conventional commits](.github/semantic.yml): `fix(parameters): ...`, `feat(event_handler): ...`, `docs(...)`. Scope is the utility name.
- Description contains `closes #<issue>` alone on its own line. Trailing text on that line breaks the related-issue check.
- Tests for the change. A bug fix adds a test that fails on `develop` and passes with the fix.
- Functional tests use the public API only, the way a customer would call it. Never test internal methods: do not call or patch private methods, do not assert on private attributes.
- Existing tests are not modified or deleted unless the PR proves the old behaviour was a bug. Say so in the description.
- `ruff`, `mypy` and the test suite green on Python 3.10 to 3.14. CI runs all five.
- Behaviour changes update the docs page and its example under `examples/<utility>/src/`.

## Things we do not do

- Add a runtime dependency. Optional features go behind an extra in `pyproject.toml`; the core stays `jmespath` and `typing-extensions`. See [ADR 0007](docs/adr/0007-lean-dependencies.md).
- Import heavy modules at module level. Cold start matters; import lazily inside the function or utility that needs it. See [ADR 0002](docs/adr/0002-every-millisecond-counts.md).
- Ship `boto3`, `botocore` or their dependencies in the Lambda layer. See [ADR 0004](docs/adr/0004-layer-and-packaging.md).
- Break or change public behaviour in a minor release. If an input we accept today is wrong, warn with `PowertoolsUserWarning` now and raise in the next major. See [ADR 0006](docs/adr/0006-zero-regression-and-compatibility.md).
- Duplicate a code path to add a variant (async, a new event shape). Share the logic and keep the difference to the call site.
- Change `tests/events/*.json` fixtures in a way that hides a bug. Add a new fixture instead.
- Use threads, background work or anything that assumes the process outlives the invocation. See [ADR 0001](docs/adr/0001-lambda-first.md).

## Verifying your change

- Run the tests yourself and read the output. Do not describe runs you did not do.
- If the change touches an AWS service integration (Parameters, Idempotency, Batch, Data Classes shapes, Event Handler payloads), validate it against the real service or a real event and say in the PR how you did it. Mocks prove the logic, not the contract.
- If you used an AI assistant, say so in the PR. We welcome it. What we ask is the verification above, done by you.

## Where things are

| Need | Look at |
| --- | --- |
| Utility code | `aws_lambda_powertools/<utility>/` or `aws_lambda_powertools/utilities/<utility>/` |
| Tests | `tests/unit/<utility>/`, `tests/functional/<utility>/`, `tests/performance/` |
| Sample events | `tests/events/` |
| Docs and examples | `docs/<area>/<utility>.md`, `examples/<utility>/src/` |
| Project premises | `docs/adr/` |
| Layer build | `layer_v3/` |
| Maintainer process | [MAINTAINERS.md](MAINTAINERS.md), [docs/maintainers.md](docs/maintainers.md) |
