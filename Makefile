.PHONY: target dev format lint test coverage-html pr  build build-docs build-docs-api build-docs-website
.PHONY: docs-local docs-api-local security-baseline complexity-baseline release-prod release-test release

target:
	@$(MAKE) pr

dev:
	pip install --upgrade pip pre-commit poetry
	@$(MAKE) dev-version-plugin
	poetry install --extras "all redis datamasking"
	pre-commit install

dev-quality-code:
	pip install --upgrade pip pre-commit poetry
	poetry install --extras "all redis datamasking"
	pre-commit install

dev-gitpod:
	pip install --upgrade pip poetry
	poetry install --extras "all redis datamasking"
	pre-commit install

format:
	poetry run black aws_lambda_powertools tests examples

lint: format
	poetry run ruff check aws_lambda_powertools tests examples

lint-docs:
	docker run -v ${PWD}:/markdown 06kellyjac/markdownlint-cli "docs"

lint-docs-fix:
	docker run -v ${PWD}:/markdown 06kellyjac/markdownlint-cli --fix "docs"

test:
	poetry run pytest -m "not perf" --ignore tests/e2e --cov=aws_lambda_powertools --cov-report=xml
	poetry run pytest --cache-clear tests/performance

test-dependencies:
	poetry run nox --error-on-external-run --reuse-venv=yes --non-interactive

test-pydanticv2:
	poetry run pytest -m "not perf" --ignore tests/e2e

unit-test:
	poetry run pytest tests/unit

e2e-test:
	poetry run pytest tests/e2e

coverage-html:
	poetry run pytest -m "not perf" --ignore tests/e2e --cov=aws_lambda_powertools --cov-report=html

pre-commit:
	pre-commit run --show-diff-on-failure

pr: lint lint-docs mypy pre-commit test security-baseline complexity-baseline

build: pr
	poetry build

release-docs:
	@echo "Rebuilding docs"
	rm -rf site api
	@echo "Updating website docs"
	poetry run mike deploy --push --update-aliases ${VERSION} ${ALIAS}
	@echo "Building API docs"
	@$(MAKE) build-docs-api VERSION=${VERSION}

build-docs-api:
	poetry run pdoc --html --output-dir ./api/ ./aws_lambda_powertools --force
	mv -f ./api/aws_lambda_powertools/* ./api/
	rm -rf ./api/aws_lambda_powertools
	mkdir ${VERSION} && cp -R api ${VERSION}

docs-local:
	poetry run mkdocs serve

docs-local-docker:
	docker build -t squidfunk/mkdocs-material ./docs/
	docker run --rm -it -p 8000:8000 -v ${PWD}:/docs squidfunk/mkdocs-material

docs-api-local:
	poetry run pdoc --http : aws_lambda_powertools

security-baseline:
	poetry run bandit --baseline bandit.baseline -r aws_lambda_powertools

complexity-baseline:
	$(info Maintenability index)
	poetry run radon mi aws_lambda_powertools
	$(info Cyclomatic complexity index)
	poetry run xenon --max-absolute C --max-modules A --max-average A aws_lambda_powertools --exclude aws_lambda_powertools/shared/json_encoder.py,aws_lambda_powertools/utilities/validation/base.py

#
# Use `poetry version <major>/<minor></patch>` for version bump
#
release-prod:
	poetry config pypi-token.pypi ${PYPI_TOKEN}
	poetry publish -n

release-test:
	poetry config repositories.testpypi https://test.pypi.org/legacy
	poetry config pypi-token.pypi ${PYPI_TEST_TOKEN}
	poetry publish --repository testpypi -n

release: pr
	poetry build
	$(MAKE) release-test
	$(MAKE) release-prod

changelog:
	git fetch --tags origin
	CURRENT_VERSION=$(shell git describe --abbrev=0 --tag) ;\
	echo "[+] Pre-generating CHANGELOG for tag: $$CURRENT_VERSION" ;\
	docker run -v "${PWD}":/workdir quay.io/git-chglog/git-chglog:0.15.1 > CHANGELOG.md

mypy:
	poetry run mypy --pretty aws_lambda_powertools examples


dev-version-plugin:
	poetry self add git+https://github.com/monim67/poetry-bumpversion@348de6f247222e2953d649932426e63492e0a6bf
