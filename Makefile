.PHONY: target dev format lint test coverage-html pr  build build-docs build-docs-api build-docs-website
.PHONY: docs-local docs-api-local security-baseline complexity-baseline release-prod release-test release

target:
	@$(MAKE) pr

dev:
	pip install --upgrade pip poetry pre-commit
	poetry install --extras "pydantic"
	pre-commit install

format:
	poetry run isort aws_lambda_powertools tests
	poetry run black aws_lambda_powertools tests

lint: format
	poetry run flake8 aws_lambda_powertools/* tests/*

test:
	poetry run pytest -m "not perf" --cov=aws_lambda_powertools --cov-report=xml
	poetry run pytest --cache-clear tests/performance

coverage-html:
	poetry run pytest -m "not perf" --cov=aws_lambda_powertools --cov-report=html

pr: lint test security-baseline complexity-baseline

build: pr
	poetry build

build-docs:
	@$(MAKE) build-docs-website
	@$(MAKE) build-docs-api

build-docs-api: dev
	mkdir -p dist/api
	poetry run pdoc --html --output-dir dist/api/ ./aws_lambda_powertools --force
	mv -f dist/api/aws_lambda_powertools/* dist/api/
	rm -rf dist/api/aws_lambda_powertools

build-docs-website: dev
	mkdir -p dist
	poetry run mkdocs build
	cp -R site/* dist/

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
	poetry run xenon --max-absolute C --max-modules A --max-average A aws_lambda_powertools

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
