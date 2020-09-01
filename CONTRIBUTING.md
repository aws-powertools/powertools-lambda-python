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
3. You open a [RFC issue](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=RFC%2C+triage&template=rfc.md&title=RFC%3A+) to discuss any significant work - we would hate for your time to be wasted.

### Dev setup

To send us a pull request, please follow these steps:

1. Fork the repository.
2. Install dependencies in a virtual env with poetry, and pre-commit hooks: `make dev`
3. Create a new branch to focus on the specific change you are contributing e.g. `improv/logger-debug-sampling`
4. Run all tests, and code baseline checks: `make pr`
    - Git hooks will run linting and formatting while `make pr` run deep checks that also run in the CI process
4. Commit to your fork using clear commit messages.
5. Send us a pull request with a [conventional semantic title](https://github.com/awslabs/aws-lambda-powertools-python/pull/67), and answering any default questions in the pull request interface.
6. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/) and
[creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

#### Local documentation

You might find useful to run both the documentation website and the API reference locally while contributing:

* **API reference**: `make docs-api-local`
* **Docs website**: `make dev-docs` to install deps, and `make docs-local` to run it thereafter

### Conventions

Category | Convention
------------------------------------------------- | ---------------------------------------------------------------------------------
**Docstring** |  We use a slight variation of numpy convention with markdown to help generate more readable API references.
**Style guide** | We use black as well as flake8 extensions to enforce beyond good practices [PEP8](https://pep8.org/). We strive to make use of type annotation as much as possible, but don't overdo in creating custom types.
**Core utilities** | Core utilities use a Class, always accept `service` as a constructor parameter, can work in isolation, and are also available in other languages implementation.
**Utilities** | Utilities are not as strict as core and focus on solving a developer experience problem while following the project [Tenets](https://awslabs.github.io/aws-lambda-powertools-python/#tenets).
**Exceptions** | Specific exceptions live within utilities themselves and use `Error` suffix e.g. `MetricUnitError`.
**Git commits** | We follow [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/). These are not enforced as we squash and merge PRs, but PR titles are enforced during CI.
**Documentation** | API reference docs are generated from docstrings which should have Examples section to allow developers to have what they need within their own IDE. Documentation website covers the wider usage, tips, and strive to be concise.

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

* You did not install the local dev environment yet
    - You can install dev deps with `make dev` command
* The code in the repository is raising an exception while the `pdoc` is scanning the codebase
    - Unfortunately, this exception is not shown to you, but if you run, `poetry run pdoc --pdf aws_lambda_powertools`, the exception is shown and you can prevent the exception from being raised
    - Once resolved the documentation should load correctly again

## Licensing

See the [LICENSE](LICENSE) file for our project's licensing. We will ask you to confirm the licensing of your contribution.

We may ask you to sign a [Contributor License Agreement (CLA)](http://en.wikipedia.org/wiki/Contributor_License_Agreement) for larger changes.
