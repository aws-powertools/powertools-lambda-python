
target:
	@$(MAKE) pr

dev:
	pip install --upgrade pip poetry
	poetry install

dev-docs:
	cd docs && npm install

format:
	poetry run isort -rc .
	poetry run black aws_lambda_powertools
	poetry run black tests

lint: format
	poetry run flake8

test:
	poetry run pytest -vvv

coverage-html:
	poetry run pytest --cov-report html

pr: lint test security-baseline complexity-baseline

build: pr
	poetry run build

docs: dev
	$(MAKE) build-docs
	poetry run pdoc --html --output-dir docs/public/api ./aws_lambda_powertools --force

docs-api: dev
	poetry run pdoc --html --output-dir docs/public/api ./aws_lambda_powertools --force

docs-dev:
	poetry run pdoc --http : aws_lambda_powertools

build-docs: dev-docs
	cd docs && npm run build

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

build-linux-wheels:
	poetry build
	docker run --env PLAT=manylinux1_x86_64 --rm -it -v ${PWD}:/io -w /io quay.io/pypa/manylinux1_x86_64 /io/build_linux_wheels.sh
	cp ./wheelhouse/* dist/ && rm -rf wheelhouse

release:
	$(MAKE) build-linux-wheels
	$(MAKE) release-test
	$(MAKE) release-prod
