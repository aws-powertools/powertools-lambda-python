# Shared dependencies
python_requirement(
    name="powertools",
    requirements=["aws-lambda-powertools[all]==3.4.0"],
)

# API Lambda function
python_sources(
    name="api_sources",
    sources=["api/*.py"],
)

pex_binary(
    name="api_lambda",
    entry_point="api/handler.py:lambda_handler",
    dependencies=[":api_sources", ":powertools"],
    platforms=["linux_x86_64-cp-39-cp39"],
)

# Worker Lambda function
python_sources(
    name="worker_sources",
    sources=["worker/*.py"],
)

pex_binary(
    name="worker_lambda",
    entry_point="worker/handler.py:lambda_handler",
    dependencies=[":worker_sources", ":powertools"],
    platforms=["linux_x86_64-cp-39-cp39"],
)
