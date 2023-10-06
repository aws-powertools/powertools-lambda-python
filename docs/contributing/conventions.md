---
title: Conventions
description: General conventions and practices that are applicable throughout to Powertools for AWS Lambda (Python)
---

<!-- markdownlint-disable MD043 -->

## General terminology and practices

These are common conventions we keep on building as the project gains new contributors and grows in complexity.

As we gather more concrete examples, this page will have one section for each category to demonstrate a before and after.

| Category              | Convention                                                                                                                                                                                                                                                                  |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Docstring**         | We use [Numpy convention](https://numpydoc.readthedocs.io/en/latest/format.html){target="_blank"} with markdown to help generate more readable API references. For public APIs, we always include at least one **Example** to ease everyone's experience when using an IDE. |
| **Style guide**       | We use black and [Ruff](https://beta.ruff.rs/docs/) to enforce beyond good practices [PEP8](https://pep8.org/). We use type annotations and enforce static type checking at CI (mypy).                                                                                      |
| **Core utilities**    | Core utilities always accept `service` as a constructor parameter, can work in isolation, and are also available in other languages implementation.                                                                                                                         |
| **Utilities**         | Utilities are not as strict as core and focus on community needs: development productivity, industry leading practices, etc. Both core and general utilities follow our [Tenets](https://docs.powertools.aws.dev/lambda/python/#tenets).                                    |
| **Exceptions**        | Specific exceptions live within utilities themselves and use `Error` suffix e.g. `MetricUnitError`.                                                                                                                                                                         |
| **Git commits**       | We follow [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/). We do not enforce conventional commits on contributors to lower the entry bar. Instead, we enforce a conventional PR title so our label automation and changelog are generated correctly. |
| **API documentation** | API reference docs are generated from docstrings which should have Examples section to allow developers to have what they need within their own IDE. Documentation website covers the wider usage, tips, and strive to be concise.                                          |
| **Documentation**     | We treat it like a product. We sub-divide content aimed at getting started (80% of customers) vs advanced usage (20%). We also ensure customers know how to unit test their code when using our features.                                                                   |

## Testing definition

We group tests in different categories

| Test              | When to write                                                                                         | Notes                                                                                                                                 | Speed                                             |
| ----------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Unit tests        | Verify the smallest possible unit works.                                                              | Networking access is prohibited. Prefer Functional tests given our complexity.                                                        | Lightning fast (nsec to ms)                       |
| Functional tests  | Guarantee functionality works as expected. It's a subset of integration test covering multiple units. | No external dependency. Prefer Fake implementations (in-memory) over Mocks and Stubs.                                                 | Fast (ms to few seconds at worst)                 |
| End-to-end tests  | Gain confidence that a Lambda function with our code operates as expected.                            | It simulates how customers configure, deploy, and run their Lambda function - Event Source configuration, IAM permissions, etc.       | Slow (minutes)                                    |
| Performance tests | Ensure critical operations won't increase latency and costs to customers.                             | CI arbitrary hardware can make it flaky. We'll resume writing perf test after we revamp our functional tests with internal utilities. | Fast to moderate (a few seconds to a few minutes) |
