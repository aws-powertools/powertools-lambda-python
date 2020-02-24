
target:
	@$(MAKE) pr

dev:
	pip install --upgrade poetry
	poetry install

format:
	poetry run isort -rc .
	poetry run black aws_lambda_powertools
	poetry run black tests

lint: format
	poetry run flake8

test:
	poetry run pytest

test-html:
	poetry run pytest --cov-report html

pr: lint test 

release: pr
	python setup.py sdist bdist_wheel
	poetry run twine upload dist/* --verbose
	rm -rf dist build	

release-test: pr
	python setup.py sdist bdist_wheel
	poetry run twine upload --repository testpypi dist/* --verbose
	rm -rf dist build	
