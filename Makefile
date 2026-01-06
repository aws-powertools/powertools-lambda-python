.PHONY: target dev format lint test coverage-html pr  build build-docs build-docs-website
.PHONY: docs-local security-baseline complexity-baseline release-prod release-test release

target:
	@$(MAKE) pr

dev:
	pip install --upgrade pip pre-commit uv
	uv sync --all-extras
	pre-commit install

dev-quality-code:
	pip install --upgrade pip pre-commit uv
	uv sync --all-extras
	pre-commit install

format-check:
	uv run ruff format aws_lambda_powertools tests examples --check

format:
	uv run ruff format aws_lambda_powertools tests examples

lint: format
	uv run ruff check aws_lambda_powertools tests examples

lint-docs:
	docker run -v ${PWD}:/markdown 06kellyjac/markdownlint-cli "docs"

lint-docs-fix:
	docker run -v ${PWD}:/markdown 06kellyjac/markdownlint-cli --fix "docs"

test:
	uv run pytest -m "not perf" --ignore tests/e2e --cov=aws_lambda_powertools --cov-report=xml
	uv run pytest --cache-clear tests/performance

test-dependencies:
	uv run nox --error-on-external-run --reuse-venv=yes --non-interactive

test-pydanticv2:
	uv run pytest -m "not perf" --ignore tests/e2e

unit-test:
	uv run pytest tests/unit

e2e-test:
	uv run pytest tests/e2e

coverage-html:
	uv run pytest -m "not perf" --ignore tests/e2e --cov=aws_lambda_powertools --cov-report=html

pre-commit:
	pre-commit run --show-diff-on-failure

pr: lint lint-docs mypy pre-commit test security-baseline complexity-baseline

build: pr
	uv build

docs-local:
	uv run mkdocs serve

docs-local-docker:
	docker build -t squidfunk/mkdocs-material ./docs/
	docker run --rm -it -p 8000:8000 -v ${PWD}:/docs squidfunk/mkdocs-material

security-baseline:
	uv run bandit --baseline bandit.baseline -r aws_lambda_powertools

complexity-baseline:
	$(info Maintenability index)
	uv run radon mi aws_lambda_powertools
	$(info Cyclomatic complexity index)
	uv run xenon --max-absolute C --max-modules A --max-average A aws_lambda_powertools --exclude aws_lambda_powertools/shared/json_encoder.py,aws_lambda_powertools/utilities/validation/base.py,aws_lambda_powertools/event_handler/api_gateway.py

#
# Use `sed` to bump version in pyproject.toml and version.py
#
release-prod:
	uv publish --token ${PYPI_TOKEN}

release-test:
	uv publish --index https://test.pypi.org/legacy --token ${PYPI_TEST_TOKEN}

release: pr
	uv build
	$(MAKE) release-test
	$(MAKE) release-prod

changelog:
	git fetch --tags origin
	CURRENT_VERSION=$(shell git describe --abbrev=0 --tag) ;\
	echo "[+] Pre-generating CHANGELOG for tag: $CURRENT_VERSION" ;\
	docker run -v "${PWD}":/workdir quay.io/git-chglog/git-chglog:0.15.1 > CHANGELOG.md

mypy:
	uv run mypy --pretty aws_lambda_powertools examples
