---
title: Versioning and maintenance policy
description: Versioning and maintenance policy for Powertools for AWS Lambda (Python)
---

<!-- markdownlint-disable MD041 MD043 MD013 -->

### Overview

This document outlines the maintenance policy for Powertools for AWS Lambda and their underlying dependencies. AWS regularly provides Powertools for AWS Lambda with updates that may contain new features, enhancements, bug fixes, security patches, or documentation updates. Updates may also address changes with dependencies, language runtimes, and operating systems. Powertools for AWS Lambda is published to package managers (e.g. PyPi, NPM, Maven, NuGet), and are available as source code on GitHub.

We recommend users to stay up-to-date with Powertools for AWS Lambda releases to keep up with the latest features, security updates, and underlying dependencies. Continued use of an unsupported Powertools for AWS Lambda version is not recommended and is done at the user’s discretion.

!!! info "For brevity, we will interchangeably refer to Powertools for AWS Lambda as "SDK" _(Software Development Toolkit)_."

### Versioning

Powertools for AWS Lambda release versions are in the form of X.Y.Z where X represents the major version. Increasing the major version of an SDK indicates that this SDK underwent significant and substantial changes to support new idioms and patterns in the language. Major versions are introduced when public interfaces _(e.g. classes, methods, types, etc.)_, behaviors, or semantics have changed. Applications need to be updated in order for them to work with the newest SDK version. It is important to update major versions carefully and in accordance with the upgrade guidelines provided by AWS.

### SDK major version lifecycle

The lifecycle for major Powertools for AWS Lambda versions consists of 5 phases, which are outlined below.

* **Developer Preview** (Phase 0) - During this phase, SDKs are not supported, should not be used in production environments, and are meant for early access and feedback purposes only. It is possible for future releases to introduce breaking changes. Once AWS identifies a release to be a stable product, it may mark it as a Release Candidate. Release Candidates are ready for GA release unless significant bugs emerge, and will receive full AWS support.
* **General Availability (GA)** (Phase 1) - During this phase, SDKs are fully supported. AWS will provide regular SDK releases that include support for new features, enhancements, as well as bug and security fixes. AWS will support the GA version of an SDK for _at least 24 months_.
* **Maintenance Announcement** (Phase 2) - AWS will make a public announcement at least 6 months before an SDK enters maintenance mode. During this period, the SDK will continue to be fully supported. Typically, maintenance mode is announced at the same time as the next major version is transitioned to GA.
* **Maintenance** (Phase 3) - During the maintenance mode, AWS limits SDK releases to address critical bug fixes and security issues only. An SDK will not receive API updates for new or existing services, or be updated to support new regions. Maintenance mode has a _default duration of 6 months_, unless otherwise specified.
* **End-of-Support** (Phase 4) - When an SDK reaches end-of support, it will no longer receive updates or releases. Previously published releases will continue to be available via public package managers and the code will remain on GitHub. The GitHub repository may be archived. Use of an SDK which has reached end-of-support is done at the user’s discretion. We recommend users upgrade to the new major version.

!!! note "Please note that the timelines shown below are illustrative and not binding"

![Maintenance policy timelines](https://docs.aws.amazon.com/images/sdkref/latest/guide/images/maint-policy.png)

### Dependency lifecycle

Most AWS SDKs have underlying dependencies, such as language runtimes, AWS Lambda runtime, or third party libraries and frameworks. These dependencies are typically tied to the language community or the vendor who owns that particular component. Each community or vendor publishes their own end-of-support schedule for their product.

The following terms are used to classify underlying third party dependencies:

* [**AWS Lambda Runtime**](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html): Examples include `nodejs20.x`, `python3.12`, etc.
* **Language Runtime**: Examples include Python 3.12, NodeJS 20, Java 17, .NET Core, etc.
* **Third party Library**: Examples include Pydantic, AWS X-Ray SDK, AWS Encryption SDK, MiddyJS, etc.

Powertools for AWS Lambda follows the [AWS Lambda Runtime deprecation policy cycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html#runtime-support-policy), when it comes to Language Runtime. This means we will stop supporting deprecated their respective Language Runtime without increasing the major SDK version.

!!! note "AWS reserves the right to stop support for an underlying dependency without increasing the major SDK version"

### Communication methods

Maintenance announcements are communicated in several ways:

* A pinned GitHub Request For Comments (RFC) issue indicating the campaign for the next major version. The RFC will outline the path to end-of-support, specify campaign timelines, and upgrade guidance.
* AWS SDK documentation, such as API reference documentation, user guides, SDK product marketing pages, and GitHub readme(s) are updated to indicate the campaign timeline and provide guidance on upgrading affected applications.
* Deprecation warnings are added to the SDKs, outlining the path to end-of-support and linking to the upgrade guide.

To see the list of available major versions of Powertools for AWS Lambda and where they are in their maintenance lifecycle, see [version support matrix](#version-support-matrix)

### Version support matrix

| SDK                              | Major version | Current Phase        | General Availability Date | Notes                                                                                                                                                                |
| -------------------------------- | ------------- | -------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Powertools for AWS Lambda Python | 2.x           | General Availability | 10/24/2022                | See [Release Notes](https://github.com/aws-powertools/powertools-lambda-python/releases/tag/v2.0.0)                                                                  |
| Powertools for AWS Lambda Python | 1.x           | End of Support       | 06/18/2020                | See [RFC](https://github.com/aws-powertools/powertools-lambda-python/issues/1459) and [upgrade guide](https://docs.powertools.aws.dev/lambda/python/latest/upgrade/) |
