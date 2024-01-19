# v9.1.18
FROM squidfunk/mkdocs-material@sha256:58eef6c68ad4c8687f7d43c560852a8f62d403126c90c919242dec93bd3eee68
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
