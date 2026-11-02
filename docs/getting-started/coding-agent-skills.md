---
title: Coding agent skills
description: Install the Powertools for AWS Lambda (Python) skill so coding agents such as Claude Code, Codex, Cursor and Gemini CLI build your Lambda functions with current knowledge of the library.
---

<!-- markdownlint-disable MD013 MD043 -->

If you build Lambda functions with a coding agent, you can install the Powertools for AWS Lambda (Python) skill so the agent works from the current documentation and the tested examples instead of what it remembers.

[Agent Skills](https://agentskills.io){target="_blank"} are directories with a `SKILL.md` file and reference material that agents load on demand. Our skill lives in this repository under [`.agents/skills/building-lambda-functions-with-powertools-python`](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/.agents/skills/building-lambda-functions-with-powertools-python){target="_blank"}. It tells the agent when Powertools applies, shows the essential patterns, lists the rules we follow (import cost, no `boto3` in the layer, one idempotency persistence layer per function, public API only) and carries one reference file per utility, generated from the documentation page you are reading on this site, examples included.

## Installation

### Claude Code

Add this repository as a plugin marketplace and install the plugin:

```bash
claude plugin marketplace add aws-powertools/powertools-lambda-python
claude plugin install powertools-lambda-python@aws-powertools
```

### Codex, Cursor, Gemini CLI and other agents

Any agent that follows the [agentskills.io](https://agentskills.io){target="_blank"} standard can install it with the [skills CLI](https://github.com/vercel-labs/skills){target="_blank"}:

```bash
npx skills add aws-powertools/powertools-lambda-python
```

### Manually

Copy the skill directory into your project's `.agents/skills/` (or `.claude/skills/` for Claude Code). The skill is plain Markdown, there is nothing to build.

## Keeping it current

The reference files are regenerated from the documentation on every change by `scripts/build_agent_skill_references.py`, and a test fails if they drift. Reinstall the skill when you upgrade Powertools for AWS Lambda (Python) to pick up new utilities and changed APIs.

## See also

- [AGENTS.md](https://github.com/aws-powertools/powertools-lambda-python/blob/develop/AGENTS.md){target="_blank"}: the rules for agents that contribute to Powertools for AWS Lambda (Python) itself
- [llms.txt](../llms.txt) and [llms-full.txt](../llms-full.txt): the documentation in a format for language models
