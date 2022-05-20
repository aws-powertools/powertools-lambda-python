
## Table of contents <!-- omit in toc -->

- [Overview](#overview)
- [Current Maintainers](#current-maintainers)
- [Emeritus](#emeritus)
- [Maintainer Responsibilities](#maintainer-responsibilities)
  - [Uphold Code of Conduct](#uphold-code-of-conduct)
  - [Prioritize Security](#prioritize-security)
  - [Review Pull Requests](#review-pull-requests)
  - [Triage New Issues](#triage-new-issues)
  - [Triage Bug Reports](#triage-bug-reports)
  - [Triage RFCs](#triage-rfcs)
  - [Releasing a new version](#releasing-a-new-version)
  - [Releasing a documentation hotfix](#releasing-a-documentation-hotfix)
  - [Maintain Overall Health of the Repo](#maintain-overall-health-of-the-repo)
  - [Manage Roadmap](#manage-roadmap)
  - [Add Continuous Integration Checks](#add-continuous-integration-checks)
  - [Negative Impact on the Project](#negative-impact-on-the-project)
  - [Becoming a maintainer](#becoming-a-maintainer)

## Overview

> **This document is currently a WORK-IN-PROGRESS**

This is document explains who the maintainers are (see below), what they do in this repo, and how they should be doing it. If you're interested in contributing, see [CONTRIBUTING](CONTRIBUTING.md).

## Current Maintainers

| Maintainer       | GitHub ID                                     | Affiliation |
| ---------------- | --------------------------------------------- | ----------- |
| Heitor Lessa     | [heitorlessa](https://github.com/heitorlessa) | Amazon      |
| Alexander Melnyk | [am29d](https://github.com/am29d)             | Amazon      |
| Michal Ploski    | [mploski](https://github.com/mploski)         | Amazon      |
| Simon Thulbourn  | [sthulb](https://github.com/sthulb)           | Amazon      |

## Emeritus

Previous active maintainers who contributed to this project.

| Maintainer        | GitHub ID                                       | Affiliation |
| ----------------- | ----------------------------------------------- | ----------- |
| Tom McCarthy      | [cakepietoast](https://github.com/cakepietoast) | MongoDB     |
| Nicolas Moutschen | [nmoutschen](https://github.com/nmoutschen)     | Amazon      |

## Maintainer Responsibilities

Maintainers are active and visible members of the community, and have [maintain-level permissions on a repository](https://docs.github.com/en/organizations/managing-access-to-your-organizations-repositories/repository-permission-levels-for-an-organization). Use those privileges to serve the community and evolve code as follows.

### Uphold Code of Conduct

Model the behavior set forward by the [Code of Conduct](CODE_OF_CONDUCT.md) and raise any violations to other maintainers and admins. There could be unusual circumstances where inappropriate behavior does not immediately fall within the [Code of Conduct](CODE_OF_CONDUCT.md). These might be nuanced and should be handled with extra care - when in doubt, do not engage and reach out to other maintainers and admins.

### Prioritize Security

Security is your number one priority. Maintainer's Github keys must be password protected securely and any reported security vulnerabilities are addressed before features or bugs.

Note that this repository is monitored and supported 24/7 by Amazon Security, see [Reporting a Vulnerability](SECURITY.md) for details.

### Review Pull Requests

> WORK-IN-PROGRESS
> TODO: cover labels, CI automation, the right to close, and a reference to FAQ on common issues.

Review pull requests regularly, comment, suggest, reject, merge and close. Accept only high quality pull-requests. Provide code reviews and guidance on incoming pull requests.

Use and enforce [semantic versioning](https://semver.org/) pull request titles, as these will be used for [CHANGELOG](CHANGELOG.md) and [Release notes](https://github.com/awslabs/aws-lambda-powertools-python/releases) - make sure they communicate their intent at human level.

### Triage New Issues

> WORK-IN-PROGRESS
> TODO: cover labels, reference to Roadmap Project Status definition, sensitive labels to defer or prioritize work, and give first priority to original authors on implementation

### Triage Bug Reports

> WORK-IN-PROGRESS
> TODO: cover different types of bugs (internal, customer-facing, upstream), reference to releasing section

### Triage RFCs

> WORK-IN-PROGRESS
> TODO: cover design proposal quality, mentoring sessions, etc.

### Releasing a new version

> WORK-IN-PROGRESS
> convert what's written in [publish.yml](.github/workflows/publish.yml)

### Releasing a documentation hotfix

> WORK-IN-PROGRESS
> convert what's written in [publish.yml](.github/workflows/publish.yml)

### Maintain Overall Health of the Repo

> TODO: Coordinate in removing `master` and renaming `develop` to `main`

Keep the `develop` branch at production quality at all times. Backport features as needed. Cut release branches and tags to enable future patches.

### Manage Roadmap

See [Roadmap section](https://awslabs.github.io/aws-lambda-powertools-python/latest/roadmap/)

Ensure the repo highlights features that should be elevated to the project roadmap. Be clear about the feature’s status, priority, target version, and whether or not it should be elevated to the roadmap.

### Add Continuous Integration Checks

Add integration checks that validate pull requests and pushes to ease the burden on Pull Request reviewers. Continuously revisit areas of improvement to reduce operational burden in all parties involved.

### Negative Impact on the Project

Actions that negatively impact the project will be handled by the admins, in coordination with other maintainers, in balance with the urgency of the issue. Examples would be [Code of Conduct](CODE_OF_CONDUCT.md) violations, deliberate harmful or malicious actions, spam, monopolization, and security risks.

### Becoming a maintainer

> WORK-IN-PROGRESS
> TODO: cover ideas of what a future process might look like for when we're ready to do it fairly and securely.
