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
