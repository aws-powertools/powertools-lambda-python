python_sources(
    name="lambda_sources",
    sources=["*.py"],
)

python_requirement(
    name="aws-lambda-powertools",
    requirements=["aws-lambda-powertools[all]==3.18.0"],
)

python_requirement(
    name="pydantic",
    requirements=["pydantic==2.10.4"],
)

python_requirement(
    name="requests",
    requirements=["requests>=2.32.4"],
)

pex_binary(
    name="lambda_function",
    entry_point="app.py:lambda_handler",
    dependencies=[
        ":lambda_sources",
        ":aws-lambda-powertools",
        ":pydantic",
        ":requests",
    ],
    platforms=["linux_x86_64-cp-39-cp39"],
)
