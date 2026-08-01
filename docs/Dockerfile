# v9.1.18
FROM squidfunk/mkdocs-material@sha256:51b87149d227691486b5f08993d28c65ca7e4990010664b697265b8e6fcd5287
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
