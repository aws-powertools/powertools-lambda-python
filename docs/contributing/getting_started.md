---
title: Your first contribution
description: All you need to know for your first contribution to Powertools for AWS Lambda (Python)
---

<!-- markdownlint-disable MD043 -->

Thank you for your interest in contributing to our project - we couldn't be more excited!

Please read through this document before submitting any issues or pull requests to ensure we have all the necessary information to effectively respond to your  contribution.

**TODO**

* [x] Types of contributions (slide as example); make a table
* [ ] How contributions are licensed etc - confirm whether we can remove CLAs mention
* [ ] Refer to licensing within sending a PR section

## Types of contributions

We consider any contribution that help this project improve everyone's experience to be valid, as long as you agree with our [tenets](../index.md#tenets){target="_blank"}, [licensing](../../LICENSE){target="_blank"}, and [Code of Conduct](#code-of-conduct).

Whether you're new contributor or a pro, we compiled a list of the common contributions to help you choose your first:

!!! info "Please check [existing open](https://github.com/aws-powertools/powertools-lambda-python/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc){target='_blank'}, or [recently closed](https://github.com/aws-powertools/powertools-lambda-python/issues?q=is%3Aissue+sort%3Aupdated-desc+is%3Aclosed){target='_blank'} issues before creating a new one."
        Each type link goes to their respective template, or Discord invite.

| Type                                                                                                                                                                                                                                                                                                | Description                                                                                                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Documentation](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=documentation%2Ctriage&projects=&template=documentation_improvements.yml&title=Docs%3A+TITLE){target="_blank" rel="nofollow"}                                                               | Ideas to make user guide or API guide clearer. It generally go from typos, diagrams, tutorials, the lack of documentation, etc.                                                                        |
| [Feature request](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=feature-request%2Ctriage&projects=&template=feature_request.yml&title=Feature+request%3A+TITLE){target="_blank" rel="nofollow"}                                                           | New functionalities or enhancements that could help you, your team, existing and future customers. Check out our [process to understand how we prioritize it](../roadmap.md#process){target="_blank"}. |
| [Design proposals](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=RFC%2Ctriage&projects=&template=rfc.yml&title=RFC%3A+TITLE){target="_blank" rel="nofollow"}                                                                                              | Request for Comments (RFC) including user experience (UX) based on a feature request to gather the community feedback, and demonstrate the art of the possible.                                        |
| [Bug report](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=bug%2Ctriage&projects=&template=bug_report.yml&title=Bug%3A+TITLE){target="_blank" rel="nofollow"}                                                                                             | A runtime error that is reproducible whether you have an idea how to solve it or not.                                                                                                                  |
| [Advocacy](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=community-content&projects=&template=share_your_work.yml&title=%5BI+Made+This%5D%3A+%3CTITLE%3E){target="_blank" rel="nofollow"}                                                                 | Share what you did with Powertools for AWS Lambda. Blog posts, workshops, presentation, sample applications, podcasts, etc.                                                                            |
| [Public reference](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=customer-reference&projects=&template=support_powertools.yml&title=%5BSupport+Powertools+for+AWS+Lambda+%28Python%29%5D%3A+%3Cyour+organization+name%3E){target="_blank" rel="nofollow"} | Become a public reference to share how you're using Powertools for AWS Lambda at your organization.                                                                                                    |
| [Discussions](https://discord.gg/B8zZKbbyET){target="_blank" rel="nofollow"}                                                                                                                                                                                                                        | Kick off a discussion on Discord, introduce yourself, and help respond to existing questions from the community.                                                                                       |
| [Static typing](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=typing%2Ctriage&projects=&template=static_typing.yml&title=Static+typing%3A+TITLE){target="_blank" rel="nofollow"}                                                                          | Improvements to increase or correct static typing coverage to ease maintenance, autocompletion, etc.                                                                                                   |
| [Technical debt](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=tech-debt%2Ctriage&projects=&template=tech_debt.yml&title=Tech+debt%3A+TITLE){target="_blank" rel="nofollow"}                                                                              | Suggest areas to address technical debt that could make maintenance easier or provide customer value faster. Generally used by maintainers and contributors.                                           |
| [Governance](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=internal%2Ctriage&projects=&template=maintenance.yml&title=Maintenance%3A+TITLE){target="_blank" rel="nofollow"}                                                                               | Ideas to improve to our governance processes, automation, and anything internal. Typically used by maintainers and regular contributors.                                                               |

## Conventions

### General terminology and practices

| Category              | Convention                                                                                                                                                                                                                                                                  |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Docstring**         | We use a slight variation of Numpy convention with markdown to help generate more readable API references.                                                                                                                                                                  |
| **Style guide**       | We use black as well as [Ruff](https://beta.ruff.rs/docs/) to enforce beyond good practices [PEP8](https://pep8.org/). We use type annotations and enforce static type checking at CI (mypy).                                                                               |
| **Core utilities**    | Core utilities use a Class, always accept `service` as a constructor parameter, can work in isolation, and are also available in other languages implementation.                                                                                                            |
| **Utilities**         | Utilities are not as strict as core and focus on solving a developer experience problem while following the project [Tenets](https://docs.powertools.aws.dev/lambda/python/#tenets).                                                                                        |
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

Looking at the existing issues is a great way to find something to contribute on. As our projects, by default, use the default GitHub issue labels (enhancement/bug/help wanted/invalid/question/documentation), [looking at any 'help wanted' issues is a great place to start](https://github.com/orgs/aws-powertools/projects/3/views/5?query=is%3Aopen+sort%3Aupdated-desc).

## Code of Conduct

!!! info "This project has adopted the [Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct){target='_blank'}"

For more information see the [Code of Conduct FAQ](https://aws.github.io/code-of-conduct-faq) or contact
<opensource-codeofconduct@amazon.com> with any additional questions or comments.

## Security issue notifications

If you discover a potential security issue in this project we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public github issue.

## Troubleshooting

### API reference documentation

When you are working on the codebase and you use the local API reference documentation to preview your changes, you might see the following message: `Module aws_lambda_powertools not found`.

This happens when:

* You did not install the local dev environment yet
    * You can install dev deps with `make dev` command
* The code in the repository is raising an exception while the `pdoc` is scanning the codebase
    * Unfortunately, this exception is not shown to you, but if you run, `poetry run pdoc --pdf aws_lambda_powertools`, the exception is shown and you can prevent the exception from being raised
    * Once resolved the documentation should load correctly again
