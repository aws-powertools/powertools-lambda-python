# v9.1.18
FROM squidfunk/mkdocs-material@sha256:6b124e13728a591607e0f087920763e405fc18861736a997896d0b253867a7b7
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
