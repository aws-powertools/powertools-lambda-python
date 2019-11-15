#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()


requirements = ["aws-xray-sdk~=2.4"]  # noqa: E501

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author="Amazon Web Services",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Python utilities for AWS Lambda functions including but not limited to tracing, logging and custom metric",
    install_requires=requirements,
    license="Apache Software License",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="aws_lambda_powertools",
    name="aws_lambda_powertools",
    packages=find_packages(),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    version="0.1.0",
    zip_safe=False,
)
