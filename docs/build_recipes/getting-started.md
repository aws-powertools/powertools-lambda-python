---
title: Getting Started
description: Prerequisites and setup for building Lambda functions with Powertools
---

<!-- markdownlint-disable MD043 -->

## Prerequisites

Before using any of these recipes, ensure you have:

* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html){target="_blank"} configured
* Python 3.10+ installed
* Your preferred build tool installed (see individual recipes)

## Choosing the right tool

Each build tool has its strengths and is optimized for different use cases. Consider your project complexity, team preferences, and deployment requirements when selecting the best approach.

| Tool                  | Best for                          | Considerations                              |
| --------------------- | --------------------------------- | ------------------------------------------- |
| **[pip](build-with-pip.md)**       | Simple projects, CI/CD            | Lightweight, universal                      |
| **[poetry](build-with-poetry.md)** | Modern Python projects            | Excellent dependency management, lock files |
| **[uv](build-with-uv.md)**         | Fast builds, performance-critical | Extremely fast, Rust-based                  |
| **[pants](build-with-pants.md)**   | Monorepos, complex projects       | Advanced build system, incremental builds   |
| **[SAM](build-with-sam.md)**       | AWS-native deployments            | Integrated with AWS, local testing          |
| **[CDK](build-with-cdk.md)**       | Infrastructure as code            | Programmatic infrastructure, type safety    |

???+ tip
    All examples in this guide are available in the [project repository](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/examples/build_recipes){target="_blank"}.
