---
title: Your first contribution
description: All you need to know for your first contribution to Powertools for AWS Lambda (Python)
---

<!-- markdownlint-disable MD043 -->

Thank you for your interest in contributing to our project - we couldn't be more excited!

!!! note "This is a living document that we will keep iterating based on everyone's feedback."

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

## Finding contributions to work on

[Besides suggesting ideas](#types-of-contributions) you think it'll improve everyone's experience, these are the most common places to find work:

| Area                                                                                                                                                                                                            | Description                                                                                                                                                                                        |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Help wanted issues](https://github.com/aws-powertools/powertools-lambda-python/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3A%22help+wanted%22+){target="_blank" rel="nofollow"}                   | These are triaged areas that we'd appreciate any level of contribution - from opinions to actual implementation.                                                                                   |
| [Missing customer feedback issues](https://github.com/aws-powertools/powertools-lambda-python/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3Aneed-customer-feedback){target="_blank" rel="nofollow"} | These are items we'd like to hear from more customers before making any decision. Sharing your thoughts, use case, or asking additional questions are great help.                                  |
| [Pending design proposals](https://github.com/aws-powertools/powertools-lambda-python/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3ARFC){target="_blank" rel="nofollow"}                            | These are feature requests that initially look good but need a RFC to enrich the discussion by validating user-experience, tradeoffs, and highlight use cases.                                     |
| [Backlog items](https://github.com/orgs/aws-powertools/projects/3/views/3?query=is%3Aopen+sort%3Aupdated-desc){target="_blank" rel="nofollow"}                                                                  | We use GitHub projects to surface what we're working on, needs triage, etc. This view shows items we already triaged but don't have the bandwidth to tackle them just yet.                         |
| [Documentation](https://docs.powertools.aws.dev/lambda/python/latest/){target="_blank"}                                                                                                                         | Documentation can always be improved. Look for areas that a better example, or a diagram, or more context helps everyone - keep in mind a diverse audience and English as a second language folks. |
| [Participate in discussions](https://discord.gg/B8zZKbbyET){target="_blank" rel="nofollow"}                                                                                                                     | There's always a discussion that could benefit others in the form of documentation, blog post, etc.                                                                                                |
| Build a sample application                                                                                                                                                                                      | Using Powertools for AWS Lambda in different contexts will give you insights on what could be made easier, which documentation could be enriched, and more.                                        |

!!! question "Still couldn't find anything that match your skill set?"
        Please reach out on [Discord](https://discord.gg/B8zZKbbyET){target="_blank" rel="nofollow"}, specially if you'd like to get mentoring for a task you'd like to take but you don't feel ready yet :)

## Sending a pull request

!!! note "First time creating a Pull Request? Keep [this document handy.](https://help.github.com/articles/creating-a-pull-request/){target='blank' rel='nofollow'}"

Before sending us a pull request, please ensure that:

* [ ] You are working against the latest source on the **develop** branch.
* [ ] You check existing [open, and recently merged](https://github.com/aws-powertools/powertools-lambda-python/pulls?q=is%3Apr+is%3Aopen%2Cmerged+sort%3Aupdated-desc){target="_blank" rel="nofollow"} pull requests to make sure someone else hasn't addressed the problem already.
* [ ] You open an [issue](https://github.com/aws-powertools/powertools-lambda-python/issues/new/choose){target="_blank" rel="nofollow"} before you begin any implementation. We value your time and bandwidth. As such, any pull requests created on non-triaged issues might not be successful.
* [ ] Create a new branch named after the change you are contributing _e.g._ `feat/logger-debug-sampling`

**Ready?**

These are the steps to send a pull request:

1. Run all formatting, linting, tests, documentation and baseline checks: `make pr`
2. Commit to your fork using clear commit messages. Don't worry about typos or format, we squash all commits during merge.
3. Send us a pull request with a [conventional semantic title](https://github.com/aws-powertools/powertools-lambda-python/pull/67).
4. Fill in the areas pre-defined in the pull request body to help expedite reviewing your work.
5. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

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
