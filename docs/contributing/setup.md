---
title: Development environment
description: Setting up your development environment for contribution
---

## Dev setup

[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-Ready--to--Code-blue?logo=gitpod)](https://gitpod.io/from-referrer/)

Firstly, [fork the repository](https://github.com/aws-powertools/powertools-lambda-python/fork).

To setup your development environment, we recommend using our pre-configured Cloud environment: <https://gitpod.io/#https://github.com/YOUR_USERNAME/aws-lambda-powertools-python>. Replace YOUR_USERNAME with your GitHub username or organization so the Cloud environment can target your fork accordingly.

Alternatively, you can use `make dev` within your local virtual environment.

To send us a pull request, please follow these steps:

1. Create a new branch to focus on the specific change you are contributing e.g. `improv/logger-debug-sampling`
2. Run all tests, and code baseline checks: `make pr`
    - Git hooks will run linting and formatting while `make pr` run deep checks that also run in the CI process
3. Commit to your fork using clear commit messages.
4. Send us a pull request with a [conventional semantic title](https://github.com/aws-powertools/powertools-lambda-python/pull/67), and answering any default questions in the pull request interface.
5. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/) and
[creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

### Local documentation

You might find useful to run both the documentation website and the API reference locally while contributing:

- **API reference**: `make docs-api-local`
- **Docs website**: `make docs-local`
    - If you prefer using Docker: `make docs-local-docker`
