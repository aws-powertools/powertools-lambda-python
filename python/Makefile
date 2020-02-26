
target:
	@$(MAKE) pr

dev:
	pip install --upgrade poetry
	poetry install

format:
	poetry run isort -rc .
	poetry run black aws_lambda_powertools
	poetry run black tests

lint:
	poetry run flake8

test:
	poetry run pytest

test-html:
	poetry run pytest --cov-report html

pr: format lint test 

build: pr
	poetry run build

#
# Use `poetry version <major>/<minor></patch>` for version bump
#
release:
	poetry config pypi-token.pypi ${PYPI_TOKEN}
	@$(MAKE) build
	poetry publish
	rm -rf dist

release-test:
	poetry config repositories.testpypi https://test.pypi.org/legacy
	poetry config pypi-token.pypi ${PYPI_TEST_TOKEN}
	@$(MAKE) build
	poetry publish --repository testpypi
	rm -rf dist
