# v9.1.18
FROM squidfunk/mkdocs-material@sha256:9af3b7e58f88c46d85fd3abfd2a8abad2bd157a8baa5ad8303d43ce0bdf098bb
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
