
target:
	@$(MAKE) pr

dev:
	pip install --upgrade pip poetry
	poetry install

format:
	poetry run isort -rc .
	poetry run black aws_lambda_powertools
	poetry run black tests

lint: format
	poetry run flake8

test:
	poetry run pytest -vvv

test-html:
	poetry run pytest --cov-report html

pr: lint test 

build: pr
	poetry run build

docs: dev
	poetry run pdoc --html --output-dir docs ./aws_lambda_powertools --force

docs-dev:
	poetry run pdoc --http : aws_lambda_powertools

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

build-linux-wheels:
	poetry build
	docker run --env PLAT=manylinux1_x86_64 --rm -it -v ${PWD}:/io -w /io quay.io/pypa/manylinux1_x86_64 /io/build_linux_wheels.sh
	cp ./wheelhouse/* dist/ && rm -rf wheelhouse

release:
	$(MAKE) build-linux-wheels
	$(MAKE) release-test
	$(MAKE) release-prod
