---
title: We Made This (Community)
description: Blog posts, tutorials, and videos about AWS Lambda Powertools created by the Powertools Community.
---

<!-- markdownlint-disable  MD001 MD043 -->

This space is dedicated to highlight our awesome community content featuring Powertools 🙏!

!!! info "[Get your content featured here](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=community-content&template=share_your_work.yml&title=%5BI+Made+This%5D%3A+%3CTITLE%3E){target="_blank"}!"

## Connect

[![Join our Discord](https://dcbadge.vercel.app/api/server/B8zZKbbyET)](https://discord.gg/B8zZKbbyET){target="_blank"}

Join us on [Discord](https://discord.gg/B8zZKbbyET){target="_blank"} to connect with the Powertools community 👋. Ask questions, learn from each other, contribute, hang out with key contributors, and more!

## Blog posts

### AWS Lambda Cookbook — Following best practices with Lambda Powertools

> **Author: [Ran Isenberg](mailto:ran.isenberg@ranthebuilder.cloud) [:material-twitter:](https://twitter.com/IsenbergRan){target="_blank"} [:material-linkedin:](https://www.linkedin.com/in/ranisenberg/){target="_blank"}**

A collection of articles explaining in detail how Lambda Powertools helps with a Serverless adoption strategy and its challenges.

* [Part 1 - Logging](https://www.ranthebuilder.cloud/post/aws-lambda-cookbook-elevate-your-handler-s-code-part-1-logging){:target="_blank"}

* [Part 2 - Observability: monitoring and tracing](https://www.ranthebuilder.cloud/post/aws-lambda-cookbook-elevate-your-handler-s-code-part-2-observability){:target="_blank"}

* [Part 3 - Business Domain Observability](https://www.ranthebuilder.cloud/post/aws-lambda-cookbook-elevate-your-handler-s-code-part-3-business-domain-observability){:target="_blank"}

* [Part 4 - Environment Variables](https://www.ranthebuilder.cloud/post/aws-lambda-cookbook-environment-variables){:target="_blank"}

* [Part 5 - Input Validation](https://www.ranthebuilder.cloud/post/aws-lambda-cookbook-elevate-your-handler-s-code-part-5-input-validation){:target="_blank"}

* [Part 6 - Configuration & Feature Flags](https://www.ranthebuilder.cloud/post/aws-lambda-cookbook-part-6-feature-flags-configuration-best-practices){:target="_blank"}

### Making all your APIs idempotent

> **Author: [Michael Walmsley](https://twitter.com/walmsles){target="_blank"}** :material-twitter:

This article dives into what idempotency means for APIs, their use cases, and how to implement them.

* [blog.walmsles.io/making-all-your-apis-idempotent](https://blog.walmsles.io/making-all-your-apis-idempotent){target="_blank"}

### Deep dive on Lambda Powertools Idempotency feature

> **Author: [Michael Walmsley](https://twitter.com/walmsles){target="_blank"}** :material-twitter:

This article describes how to best calculate your idempotency token, implementation details, and how to handle idempotency in RESTful APIs.

* [blog.walmsles.io/aws-lambda-powertools-idempotency-a-deeper-dive](https://blog.walmsles.io/aws-lambda-powertools-idempotency-a-deeper-dive){target="_blank"}

### Developing AWS Lambda functions with AWS Lambda Powertools

> **Author: [Stephan Huber](https://linkedin.com/in/sthuber90){target="_blank"}** :material-linkedin:

This article walks through how to add Powertools to an existing project, covers Tracer, Logger, Metrics, and JSON Schema Validation.

* [globaldatanet.com/tech-blog/develop-lambda-functions-with-aws-lambda-powertools](https://globaldatanet.com/tech-blog/develop-lambda-functions-with-aws-lambda-powertools){target="_blank"}

### Speed-up event-driven projects

> **Author: [Joris Conijn](https://www.linkedin.com/in/jorisconijn){target="_blank"}** :material-linkedin:

This article walks through a sample AWS EventBridge cookiecutter template presented at the AWS Community Day Netherlands 2022.

* [binx.io/2022/10/11/speedup-event-driven-projects/](https://binx.io/2022/10/11/speedup-event-driven-projects/){target="_blank"}
* [Slides](https://www.slideshare.net/JorisConijn/let-codecommit-work-for-you){target="_blank"}

### Implementing Feature Flags with AWS AppConfig and AWS Lambda Powertools

> **Author: [Ran Isenberg](mailto:ran.isenberg@ranthebuilder.cloud) [:material-twitter:](https://twitter.com/IsenbergRan){target="_blank"} [:material-linkedin:](https://www.linkedin.com/in/ranisenberg/){target="_blank"}**

This article walks through how CyberArk uses Powertools to implement Feature Flags with AWS AppConfig

* [aws.amazon.com/blogs/mt/how-cyberark-implements-feature-flags-with-aws-appconfig](https://aws.amazon.com/blogs/mt/how-cyberark-implements-feature-flags-with-aws-appconfig){target="_blank"}

## Videos

#### Building a resilient input handling with Parser

> **Author: [Ran Isenberg](mailto:ran.isenberg@ranthebuilder.cloud) [:material-twitter:](https://twitter.com/IsenbergRan){target="_blank"} [:material-linkedin:](https://www.linkedin.com/in/ranisenberg/){target="_blank"}**

When building applications with AWS Lambda it is critical to verify the data structure and validate the input due to the multiple different sources that can trigger them. In this session Ran Isenberg (CyberArk) will present one of the interesting features of AWS Lambda Powertools for python: the parser.

In this session you will learn how to increase code quality, extensibility and testability, boost you productivity and ship rock solid apps to production.

<iframe src="https://player.twitch.tv/?video=1034744364&parent=awslabs.github.io&autoplay=false" frameborder="0" allowfullscreen="true" scrolling="no" height="378" width="620"></iframe>

#### Talk DEV to me | Feature Flags with AWS Lambda Powertools

> **Author: [Ran Isenberg](mailto:ran.isenberg@ranthebuilder.cloud) [:material-twitter:](https://twitter.com/IsenbergRan){target="_blank"} [:material-linkedin:](https://www.linkedin.com/in/ranisenberg/){target="_blank"}**

A deep dive in the [Feature Flags](./utilities/feature_flags.md){target="_blank"} feature along with tips and tricks.

<iframe src="https://player.twitch.tv/?video=1174133534&parent=awslabs.github.io&autoplay=false" frameborder="0" allowfullscreen="true" scrolling="no" height="378" width="620"></iframe>

#### Level Up Your CI/CD With Smart AWS Feature Flags

> **Author: [Ran Isenberg](mailto:ran.isenberg@ranthebuilder.cloud) [:material-twitter:](https://twitter.com/IsenbergRan){target="_blank"} [:material-linkedin:](https://www.linkedin.com/in/ranisenberg/){target="_blank"}**

Feature flags can improve your CI/CD process by enabling capabilities otherwise not possible, thus making them an enabler of DevOps and a crucial part of continuous integration. Partial rollouts, A/B testing, and the ability to quickly change a configuration without redeploying code are advantages you gain by using features flags.

In this talk, you will learn the added value of using feature flags as part of your CI/CD process and how AWS Lambda Powertools can help with that.

<iframe width="620" height="378" src="https://www.youtube.com/embed/3IT4UzN9Jds" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## Workshops

### Introduction to Lambda Powertools

> **Author: [Michael Walmsley](https://twitter.com/walmsles){target="_blank"}** :material-twitter:

This repo contains documentation for a live coding workshop for the AWS Programming and Tools Meetup in Melbourne. The workshop will start with the SAM Cli "Hello World" example API project.

Throughout the labs we will introduce each of the AWS Lambda Powertools Core utilities to showcase how simple they are to use and adopt for all your projects, and how powerful they are at bringing you closer to the Well Architected Serverless Lens.

* :material-github: [github.com/walmsles/lambda-powertools-coding-workshop](https://github.com/walmsles/lambda-powertools-coding-workshop){target="_blank"}

**Walk-through video**

<iframe width="620" height="378" src="https://www.youtube.com/embed/N1r7J3Xztsc" title="YouTube video player" frameborder="0" allow="accelerometer;  clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## Sample projects

### Complete Lambda Handler Cookbook

> **Author: [Ran Isenberg](mailto:ran.isenberg@ranthebuilder.cloud) [:material-twitter:](https://twitter.com/IsenbergRan){target="_blank"} [:material-linkedin:](https://www.linkedin.com/in/ranisenberg/){target="_blank"}**

This repository provides a working, deployable, open source based, AWS Lambda handler and [AWS CDK](https://aws.amazon.com/cdk/){target="_blank"} Python code.

This handler embodies Serverless best practices and has all the bells and whistles for a proper production ready handler. It uses many of the AWS Lambda Powertools utilities for Python.

:material-github: [github.com/ran-isenberg/aws-lambda-handler-cookbook](https://github.com/ran-isenberg/aws-lambda-handler-cookbook){:target="_blank"}
