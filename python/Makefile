
target:
	@$(MAKE) pr

dev:
	pipenv install
	pipenv install -d

format:
	pipenv run isort -rc .
	pipenv run black aws_lambda_powertools
	pipenv run black tests

lint: format
	pipenv run flake8

test:
	pipenv run pytest

test-html:
	pipenv run pytest --cov-report html

pr: lint test 

release: pr
	python setup.py sdist bdist_wheel
	pipenv run twine upload dist/* --verbose
	rm -rf dist build	

release-test: pr
	python setup.py sdist bdist_wheel
	pipenv run twine upload --repository testpypi dist/* --verbose
	rm -rf dist build	
