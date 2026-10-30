<!-- markdownlint-disable MD041 MD043 -->
# 0005. Tests are a contract

Status: Accepted

## Context

The test suite encodes the behaviour customers rely on. When a change makes an existing test fail, there are two possibilities: the change broke a contract, or the test was pinning a bug. Editing the test to make it pass hides which one it was. We have seen fixes land where a test expectation was flipped without evidence, and the "fix" was in fact a behaviour change.

Tests that reach into private methods and attributes are fragile in the other direction: they break on refactors that change nothing for customers, and they let a bug through as long as the internals look right.

## Decision

- An existing test is modified or deleted only when the PR demonstrates the old expectation was wrong. The description names the test, states what the old expectation asserted, and shows why that was a bug (a documented behaviour, an AWS contract, a reproduction). Otherwise the change is wrong, not the test.
- Every bug fix adds a regression test that fails on `develop` without the fix and passes with it.
- Tests exercise the public API: the decorators, classes and functions customers import. They do not call private methods, patch private attributes or assert on internal state. If behaviour cannot be observed through the public API, that is a design question for the PR, not a reason to poke inside.
- Sample events in `tests/events/` reflect what the AWS service really sends. When a fixture turns out to be wrong (for example a field the service never includes), we add a correct fixture rather than editing the old one to keep old tests green.
- Coverage of the lines a PR adds is checked before merge. New code without tests does not land.
- Known flaky tests are tracked and re-run; they are not deleted or loosened to pass.

## Consequences

- Reviews start by reading the test diff. A green suite with modified expectations gets more scrutiny, not less.
- Some fixes take longer because the bug has to be reproduced through the public surface first. That reproduction is the most valuable part of the PR.
- Refactors that change no behaviour should leave `tests/` untouched.

## When reviewing or writing a change

Run `git diff develop -- tests/` first. For every removed or changed assertion, find the sentence in the PR that justifies it. If there is none, ask.
