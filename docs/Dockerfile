# v9.1.18
FROM squidfunk/mkdocs-material@sha256:065f3afa6121fba3a02d03c8f393610e1a2de837548e349b884c02779e6196e5
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
