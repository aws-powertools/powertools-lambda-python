<!-- markdownlint-disable MD043 MD041 -->
# Table of contents <!-- omit in toc -->

- [Contributing Guidelines](#contributing-guidelines)
    - [Reporting Bugs/Feature Requests](#reporting-bugsfeature-requests)
    - [Contributing via Pull Requests](#contributing-via-pull-requests)
        - [Dev setup](#dev-setup)
        - [Local documentation](#local-documentation)
    - [Conventions](#conventions)
        - [General terminology and practices](#general-terminology-and-practices)
        - [Testing definition](#testing-definition)
    - [Finding contributions to work on](#finding-contributions-to-work-on)
    - [Code of Conduct](#code-of-conduct)
    - [Security issue notifications](#security-issue-notifications)
    - [Troubleshooting](#troubleshooting)
        - [API reference documentation](#api-reference-documentation)
    - [Licensing](#licensing)

# Contributing Guidelines

Thank you for your interest in contributing to our project. Whether it's a bug report, new feature, correction, or additional
documentation, we greatly value feedback and contributions from our community.

Please read through this document before submitting any issues or pull requests to ensure we have all the necessary
information to effectively respond to your bug report or contribution.

## Reporting Bugs/Feature Requests

We welcome you to use the GitHub issue tracker to report bugs, suggest features, or documentation improvements.

When filing an issue, please check existing open, or recently closed, issues to make sure somebody else hasn't already
reported the issue. Please try to include as much information as you can.

## Contributing via Pull Requests

Contributions via pull requests are much appreciated. Before sending us a pull request, please ensure that:

1. You are working against the latest source on the **develop** branch.
2. You check existing open, and recently merged pull requests to make sure someone else hasn't addressed the problem already.
3. You open an [issue](https://github.com/awslabs/aws-lambda-powertools-python/issues/new/choose) before you begin any implementation. We value your time and bandwidth. As such, any pull requests created on non-triaged issues might not be successful.

### Dev setup

[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/from-referrer/)

Firstly, [fork the repository](https://github.com/awslabs/aws-lambda-powertools-python/fork).

To setup your development environment, we recommend using our pre-configured Cloud environment: <https://gitpod.io/#https://github.com/YOUR_USERNAME/aws-lambda-powertools-python>. Replace YOUR_USERNAME with your GitHub username or organization so the Cloud environment can target your fork accordingly.

Alternatively, you can use `make dev` within your local virtual environment.

To send us a pull request, please follow these steps:

1. Create a new branch to focus on the specific change you are contributing e.g. `improv/logger-debug-sampling`
2. Run all tests, and code baseline checks: `make pr`
    - Git hooks will run linting and formatting while `make pr` run deep checks that also run in the CI process
3. Commit to your fork using clear commit messages.
4. Send us a pull request with a [conventional semantic title](https://github.com/awslabs/aws-lambda-powertools-python/pull/67), and answering any default questions in the pull request interface.
5. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/) and
[creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

### Local documentation

You might find useful to run both the documentation website and the API reference locally while contributing:

- **API reference**: `make docs-api-local`
- **Docs website**: `make docs-local`
    - If you prefer using Docker: `make docs-local-docker`

## Conventions

### General terminology and practices

| Category              | Convention                                                                                                                                                                                                                                                                  |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Docstring**         | We use a slight variation of Numpy convention with markdown to help generate more readable API references.                                                                                                                                                                  |
| **Style guide**       | We use black as well as flake8 extensions to enforce beyond good practices [PEP8](https://pep8.org/). We use type annotations and enforce static type checking at CI (mypy).                                                                                                |
| **Core utilities**    | Core utilities use a Class, always accept `service` as a constructor parameter, can work in isolation, and are also available in other languages implementation.                                                                                                            |
| **Utilities**         | Utilities are not as strict as core and focus on solving a developer experience problem while following the project [Tenets](https://awslabs.github.io/aws-lambda-powertools-python/#tenets).                                                                               |
| **Exceptions**        | Specific exceptions live within utilities themselves and use `Error` suffix e.g. `MetricUnitError`.                                                                                                                                                                         |
| **Git commits**       | We follow [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/). We do not enforce conventional commits on contributors to lower the entry bar. Instead, we enforce a conventional PR title so our label automation and changelog are generated correctly. |
| **API documentation** | API reference docs are generated from docstrings which should have Examples section to allow developers to have what they need within their own IDE. Documentation website covers the wider usage, tips, and strive to be concise.                                          |
| **Documentation**     | We treat it like a product. We sub-divide content aimed at getting started (80% of customers) vs advanced usage (20%). We also ensure customers know how to unit test their code when using our features.                                                                   |

### Testing definition

We group tests in different categories

| Test              | When to write                                                                                         | Notes                                                                                                                           | Speed                                             |
| ----------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Unit tests        | Verify the smallest possible unit works.                                                              | Networking access is prohibited. Prefer Functional tests given our complexity.                                                  | Lightning fast (nsec to ms)                       |
| Functional tests  | Guarantee functionality works as expected. It's a subset of integration test covering multiple units. | No external dependency. Prefer Fake implementations (in-memory) over Mocks and Stubs.                                           | Fast (ms to few seconds at worst)                 |
| Integration tests | Gain confidence that code works with one or more external dependencies.                               | No need for a Lambda function. Use our code base against an external dependency _e.g., fetch an existing SSM parameter_.        | Moderate to slow (a few minutes)                  |
| End-to-end tests  | Gain confidence that a Lambda function with our code operates as expected.                            | It simulates how customers configure, deploy, and run their Lambda function - Event Source configuration, IAM permissions, etc. | Slow (minutes)                                    |
| Performance tests | Ensure critical operations won't increase latency and costs to customers.                             | CI arbitrary hardware can make it flaky. We'll resume writing perf test after our new Integ/End have significant coverage.      | Fast to moderate (a few seconds to a few minutes) |

**NOTE**: Functional tests are mandatory. We have plans to create a guide on how to create these different tests. Maintainers will help indicate whether additional tests are necessary and provide assistance as required.

## Finding contributions to work on

Looking at the existing issues is a great way to find something to contribute on. As our projects, by default, use the default GitHub issue labels (enhancement/bug/help wanted/invalid/question/documentation), looking at any 'help wanted' issues is a great place to start.

## Code of Conduct

This project has adopted the [Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct).
For more information see the [Code of Conduct FAQ](https://aws.github.io/code-of-conduct-faq) or contact
opensource-codeofconduct@amazon.com with any additional questions or comments.

## Security issue notifications

If you discover a potential security issue in this project we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public github issue.

## Troubleshooting

### API reference documentation

When you are working on the codebase and you use the local API reference documentation to preview your changes, you might see the following message: `Module aws_lambda_powertools not found`.

This happens when:

- You did not install the local dev environment yet
    - You can install dev deps with `make dev` command
- The code in the repository is raising an exception while the `pdoc` is scanning the codebase
    - Unfortunately, this exception is not shown to you, but if you run, `poetry run pdoc --pdf aws_lambda_powertools`, the exception is shown and you can prevent the exception from being raised
    - Once resolved the documentation should load correctly again

## Licensing

See the [LICENSE](LICENSE) file for our project's licensing. We will ask you to confirm the licensing of your contribution.

We may ask you to sign a [Contributor License Agreement (CLA)](http://en.wikipedia.org/wiki/Contributor_License_Agreement) for larger changes.
