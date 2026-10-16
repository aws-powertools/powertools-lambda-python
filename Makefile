.PHONY: target dev dev-quality-code format format-check lint lint-check test coverage-html pr build build-docs build-docs-website
.PHONY: docs-local security-baseline complexity-baseline release-prod release-test release

target:
	@$(MAKE) pr

dev: dev-quality-code
	uv run --locked pre-commit install

dev-quality-code:
	uv sync --locked --extra all --extra redis --extra datamasking --extra valkey

format-check:
	uv run --locked ruff format aws_lambda_powertools tests examples --check

format:
	uv run --locked ruff format aws_lambda_powertools tests examples

lint: format
	$(MAKE) lint-check

lint-check:
	uv run --locked ruff check aws_lambda_powertools tests examples

lint-docs:
	docker run -v ${PWD}:/markdown 06kellyjac/markdownlint-cli "docs"

lint-docs-fix:
	docker run -v ${PWD}:/markdown 06kellyjac/markdownlint-cli --fix "docs"

test:
	uv run --locked pytest -m "not perf" --ignore tests/e2e --cov=aws_lambda_powertools --cov-report=xml
	uv run --locked pytest --cache-clear tests/performance

test-dependencies:
	uv run --locked nox --error-on-external-run --reuse-venv=no --non-interactive

test-pydanticv2:
	uv run --locked pytest -m "not perf" --ignore tests/e2e

unit-test:
	uv run --locked pytest tests/unit

e2e-test:
	uv run --locked pytest tests/e2e

coverage-html:
	uv run --locked pytest -m "not perf" --ignore tests/e2e --cov=aws_lambda_powertools --cov-report=html

pre-commit:
	uv run --locked pre-commit run --show-diff-on-failure

pr: lint lint-docs mypy pre-commit test security-baseline complexity-baseline

build: pr
	uv build --no-sources

docs-local:
	uv run --locked mkdocs serve

docs-local-docker:
	docker build -t squidfunk/mkdocs-material ./docs/
	docker run --rm -it -p 8000:8000 -v ${PWD}:/docs squidfunk/mkdocs-material

security-baseline:
	uv run --locked bandit --baseline bandit.baseline -r aws_lambda_powertools

complexity-baseline:
	$(info Maintenability index)
	uv run --locked radon mi aws_lambda_powertools
	$(info Cyclomatic complexity index)
	uv run --locked xenon --max-absolute C --max-modules A --max-average A aws_lambda_powertools --exclude aws_lambda_powertools/shared/json_encoder.py,aws_lambda_powertools/utilities/validation/base.py,aws_lambda_powertools/event_handler/api_gateway.py

#
# Release workflows update the package version before building.
#
release-prod:
	UV_PUBLISH_TOKEN="${PYPI_TOKEN}" uv publish

release-test:
	UV_PUBLISH_TOKEN="${PYPI_TEST_TOKEN}" uv publish --publish-url https://test.pypi.org/legacy/

release: pr
	uv build --no-sources
	$(MAKE) release-test
	$(MAKE) release-prod

changelog:
	git fetch --tags origin
	CURRENT_VERSION=$(shell git describe --abbrev=0 --tag) ;\
	echo "[+] Pre-generating CHANGELOG for tag: $$CURRENT_VERSION" ;\
	docker run -v "${PWD}":/workdir quay.io/git-chglog/git-chglog:0.15.1 > CHANGELOG.md

mypy:
	uv run --locked mypy --pretty aws_lambda_powertools examples

ty:
	uv run --locked ty check .
