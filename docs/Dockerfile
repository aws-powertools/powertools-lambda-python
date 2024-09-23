# v9.1.18
FROM squidfunk/mkdocs-material@sha256:22a429f602f2f616ff12ddc19bdcaae5f2096086a79c529fddd5472bdcb46165
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
