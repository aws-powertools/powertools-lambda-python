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

1. You are working against the latest source on the *develop* branch.
2. You check existing open, and recently merged, pull requests to make sure someone else hasn't addressed the problem already.
3. You open a RFC issue to discuss any significant work - we would hate for your time to be wasted.

### Dev setup

If you prefer not to use your current IDE and environment, you can use a pre-configured browser IDE with all tools installed - [![Launch IDE](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/awslabs/aws-lambda-powertools-python)

To send us a pull request, please follow these steps:

1. Fork the repository.
2. Install dependencies in a virtual env with poetry, and pre-commit hooks: `make dev`
3. Create a new branch to focus on the specific change you are contributing e.g. `improv/logger-debug-sampling`
4. Run all tests, and code baseline checks: `make pr`
    - Git hooks will run linting and formatting while `make pr` run deep checks that also run in the CI process
4. Commit to your fork using clear commit messages.
5. Send us a pull request with a [conventional semantic title](https://github.com/awslabs/aws-lambda-powertools-python/pulls?q=is%3Apr+is%3Aclosed), and answering any default questions in the pull request interface.
6. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/) and
[creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

## Finding contributions to work on

Looking at the existing issues is a great way to find something to contribute on. As our projects, by default, use the default GitHub issue labels (enhancement/bug/help wanted/invalid/question/documentation), looking at any 'help wanted' issues is a great place to start.

## Local documentation

You might find useful to run both the documentation website and the API reference locally while contributing.

* **API reference**: `make docs-api-local`
* **Docs website**: `make dev-docs` to install deps, and `make docs-local` to run it thereafter

## Code of Conduct

This project has adopted the [Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct).
For more information see the [Code of Conduct FAQ](https://aws.github.io/code-of-conduct-faq) or contact
opensource-codeofconduct@amazon.com with any additional questions or comments.

## Security issue notifications
If you discover a potential security issue in this project we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public github issue.


## Licensing

See the [LICENSE](LICENSE) file for our project's licensing. We will ask you to confirm the licensing of your contribution.

We may ask you to sign a [Contributor License Agreement (CLA)](http://en.wikipedia.org/wiki/Contributor_License_Agreement) for larger changes.
