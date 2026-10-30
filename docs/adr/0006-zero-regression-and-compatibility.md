<!-- markdownlint-disable MD041 MD043 -->
# 0006. Zero regression and backwards compatibility

Status: Accepted

## Context

Customers upgrade Powertools through the layer or by bumping a pin, often without reading release notes. Code that worked on version N must work on N+1 within the same major.

This includes behaviour we consider wrong but never rejected: an OpenAPI extension key without the `x-` prefix, a cookie attribute we emitted incorrectly, a lenient parse. Turning those into errors in a minor release breaks running functions.

## Decision

- A minor or patch release does not break code that worked on the previous one. Public signatures, return types, emitted payload shapes and exception types are kept.
- When input we accept today is invalid, a minor release warns with `PowertoolsUserWarning` and keeps the old behaviour. The warning states what will change and when. The error arrives in the next major.
- Removal of anything public happens only in a major release, after at least one minor with a deprecation warning and a migration path in `docs/upgrade.md`.
- Bug fixes may change behaviour when the old behaviour contradicted the documentation, the type hints or the AWS contract. The PR says so explicitly and the release notes call it out.
- New optional behaviour defaults to the old behaviour. New parameters have defaults that keep existing calls unchanged.
- Each change is checked against the previous release, not only against the test suite: what the old version returned for the same input, and whether a customer could depend on it.

## Consequences

- Some wrong behaviour lives for a while behind a warning. That is the cost of not breaking people.
- Release notes distinguish fixes that change observable behaviour from fixes that do not.
- Reviews ask "what did this return before, and who might rely on it?" before accepting a change in output.

## When reviewing or writing a change

Diff the behaviour, not only the code: run the same input on the previous release and on the branch. If the output differs, decide between warning and fix, and write the answer in the PR.
