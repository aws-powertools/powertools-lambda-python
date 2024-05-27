# v9.1.18
FROM squidfunk/mkdocs-material@sha256:8a87f059a80626324d012a72dc9a7b4275e89d1d6a83d1c55fed8063cc562fab
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
