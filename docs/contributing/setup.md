---
title: Development environment
description: Setting up your development environment for contribution
---

<!-- markdownlint-disable MD043 -->

[![Join our Discord](https://img.shields.io/badge/Discord-Join_Community-7289da.svg)](https://discord.gg/B8zZKbbyET){target="_blank"}

This page describes how to setup your development environment to contribute to Powertools for AWS Lambda.

<center>
```mermaid
graph LR
    Dev["Development environment"] --> Quality["Run quality checks locally"] --> PR["Prepare pull request"] --> Collaborate
```
<i>End-to-end process</i>
</center>

## Requirements

!!! question "First time contributing to an open-source project ever?"
    Read this [introduction on how to fork and clone a project on GitHub](https://docs.github.com/en/get-started/quickstart/contributing-to-projects){target="_blank" rel="nofollow"}.

You'll need the following installed:

* [GitHub account](https://github.com/join){target="_blank" rel="nofollow"}. You'll need to be able to fork, clone, and contribute via pull request.
* [Python 3.10+](https://www.python.org/downloads/){target="_blank" rel="nofollow"}. Pick any version supported in [AWS Lambda runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).
* [Docker](https://docs.docker.com/engine/install/){target="_blank" rel="nofollow"}. We use it to run documentation linters and non-Python tooling.
* [Fork the repository](https://github.com/aws-powertools/powertools-lambda-python/fork). You'll work against your fork of this repository.

??? note "Additional requirements if running end-to-end tests"

    * [AWS CDK CLI](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_prerequisites){target="_blank"}
    * [AWS Account bootstrapped with CDK](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html){target="_blank"}
    * [AWS CLI installed and configured](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

## Local environment

You can use `make dev` to create a local virtual environment and install all dependencies locally.

!!! note "Curious about what `make dev` does under the hood?"
    We use `Make` to [automate common tasks](https://github.com/aws-powertools/powertools-lambda-python/blob/1ebe3275a5c53aed5a8eb76318e7d0af2367edfa/Makefile#L7){target="_blank" rel="nofollow"} locally and in Continuous Integration environments.

## Local documentation

You might find useful to run both the documentation website and the API reference locally while contributing:

* **Docs website**: `make docs-local`
    * If you prefer using Docker: `make docs-local-docker`
* **API reference**: `make docs-api-local`
