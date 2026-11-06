"""Build the Agent Skill reference files from the documentation.

Each reference is a documentation page with the mkdocs-only syntax removed and the
``--8<--`` snippet includes resolved, so coding agents read the same content and the
same tested examples the website shows. Run without arguments to regenerate, or with
``--check`` to fail when the committed references are out of date (used by the tests).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SKILL = ROOT / ".agents" / "skills" / "building-lambda-functions-with-powertools-python"
REFERENCES = SKILL / "references"
DOCS_URL = "https://docs.powertools.aws.dev/lambda/python/latest/"

# reference file name -> documentation pages, in order
PAGES: dict[str, list[str]] = {
    "installation": ["getting-started/install.md"],
    "logger": ["core/logger.md"],
    "tracer": ["core/tracer.md"],
    "metrics": ["core/metrics/index.md", "core/metrics/datadog.md"],
    "event-handler-rest-http": ["core/event_handler/api_gateway.md"],
    "event-handler-openapi": ["core/event_handler/openapi.md"],
    "event-handler-appsync": ["core/event_handler/appsync.md"],
    "event-handler-appsync-events": ["core/event_handler/appsync_events.md"],
    "event-handler-bedrock-agents": ["core/event_handler/bedrock_agents.md"],
    "parameters": ["utilities/parameters.md"],
    "auth-jwt-oauth2": ["utilities/auth.md", "utilities/oauth2.md"],
    "batch-processing": ["utilities/batch.md"],
    "kafka": ["utilities/kafka.md"],
    "typing": ["utilities/typing.md"],
    "validation": ["utilities/validation.md"],
    "event-source-data-classes": ["utilities/data_classes.md"],
    "parser": ["utilities/parser.md"],
    "idempotency": ["utilities/idempotency.md"],
    "circuit-breaker": ["utilities/circuit_breaker.md"],
    "data-masking": ["utilities/data_masking.md"],
    "feature-flags": ["utilities/feature_flags.md"],
    "metadata": ["utilities/metadata.md"],
    "streaming": ["utilities/streaming.md"],
    "middleware-factory": ["utilities/middleware_factory.md"],
    "jmespath-functions": ["utilities/jmespath_functions.md"],
    "lambda-managed-instances": ["lambda-features/managed-instances.md"],
    "durable-functions": ["lambda-features/durable-functions.md"],
}

DROP_SECTIONS = ("## Testing your code", "## FAQ")
FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
INCLUDE = re.compile(r'^(?P<indent>\s*)--8<--\s*"(?P<path>[^"]+)"\s*$')
TAB = re.compile(r'^(?P<indent>\s*)=== "(?P<title>[^"]+)"\s*$')
ADMONITION = re.compile(
    r'^(?P<indent>\s*)(?:!!!|\?\?\?[+-]?)(?:\s+(?P<kind>[\w-]+))?(?:\s+inline(?:\s+end)?)?(?:\s+"(?P<title>.*)")?\s*$',
)
HL_LINES = re.compile(r'\s+hl_lines="[^"]*"')
TARGET_BLANK = re.compile(r"\{[^{}]*target=[^{}]*\}")
ICON = re.compile(r":(?:material|octicons|fontawesome|simple)-[\w-]+:(?:\{[^}]*\})?")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
ATTR_LIST = re.compile(r"^\{\s*\..*\}\s*$")


def resolve_includes(text: str) -> str:
    out: list[str] = []
    for line in text.splitlines():
        match = INCLUDE.match(line)
        if not match:
            out.append(line)
            continue
        path = match.group("path").split(":")[0]
        source = ROOT / path
        if not source.exists():
            out.append(f"{match.group('indent')}# (missing snippet: {path})")
            continue
        body = source.read_text(encoding="utf-8").rstrip("\n")
        if source.suffix == ".md":
            # markdown includes can include snippets themselves
            body = resolve_includes(body).rstrip("\n")
        out.extend(
            f"{match.group('indent')}{snippet_line}" if snippet_line else "" for snippet_line in body.splitlines()
        )
    return "\n".join(out) + "\n"


def flatten_blocks(text: str) -> str:
    """Turn content tabs and admonitions into plain headings and dedent their bodies."""
    out: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        tab = TAB.match(line)
        adm = ADMONITION.match(line)
        if tab or adm:
            indent = (tab or adm).group("indent")  # type: ignore[union-attr]
            if tab:
                out.append(f"{indent}**{tab.group('title')}**")
            else:
                kind = (adm.group("kind") or "note").capitalize()  # type: ignore[union-attr]
                title = adm.group("title")  # type: ignore[union-attr]
                out.append(f"{indent}> **{kind}{': ' + title if title else ''}**")
            out.append("")
            i += 1
            body_indent = indent + "    "
            while i < len(lines) and (lines[i].startswith(body_indent) or not lines[i].strip()):
                out.append(lines[i][len(body_indent) :] if lines[i].strip() else "")
                i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out) + "\n"


def drop_sections(text: str) -> str:
    out: list[str] = []
    skipping = False
    for line in text.splitlines():
        if line.startswith("## "):
            skipping = line.strip() in DROP_SECTIONS
        if not skipping:
            out.append(line)
    return "\n".join(out) + "\n"


def clean(text: str) -> str:
    text = FRONT_MATTER.sub("", text)
    text = HTML_COMMENT.sub("", text)
    text = HL_LINES.sub("", text)
    text = TARGET_BLANK.sub("", text)
    text = ICON.sub("", text)
    text = "\n".join(line for line in text.splitlines() if not ATTR_LIST.match(line))
    text = "\n".join(line.rstrip() for line in text.splitlines())  # keep the trailing-whitespace hook idempotent
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def build_reference(name: str, pages: list[str]) -> str:
    parts = [
        f"<!-- Generated by scripts/build_agent_skill_references.py from {', '.join(pages)}. Do not edit by hand. -->",
        f"# {name.replace('-', ' ').title()}",
        "",
        "Source of truth: " + ", ".join(f"{DOCS_URL}{p.removesuffix('.md').removesuffix('/index')}/" for p in pages),
        "",
    ]
    for page in pages:
        text = (DOCS / page).read_text(encoding="utf-8")
        text = resolve_includes(text)
        text = TARGET_BLANK.sub("", text)
        # tabs and admonitions nest; flatten until nothing changes
        previous = None
        while previous != text:
            previous, text = text, flatten_blocks(text)
        text = drop_sections(text)
        parts.append(clean(text))
    return "\n".join(parts)


def main(check: bool) -> int:
    REFERENCES.mkdir(parents=True, exist_ok=True)
    stale: list[str] = []
    for name, pages in PAGES.items():
        content = build_reference(name, pages)
        target = REFERENCES / f"{name}.md"
        if check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                stale.append(target.name)
        else:
            target.write_text(content, encoding="utf-8")
    expected = {f"{name}.md" for name in PAGES}
    extra = sorted(p.name for p in REFERENCES.glob("*.md") if p.name not in expected)
    if check:
        if stale or extra:
            print("Agent skill references are out of date. Run: uv run python scripts/build_agent_skill_references.py")
            for item in stale:
                print(f"  stale: {item}")
            for item in extra:
                print(f"  unexpected: {item}")
            return 1
        print("Agent skill references are up to date.")
        return 0
    for item in extra:
        (REFERENCES / item).unlink()
    print(f"Wrote {len(PAGES)} references to {REFERENCES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
