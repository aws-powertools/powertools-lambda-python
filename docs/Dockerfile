# v9.1.18
FROM squidfunk/mkdocs-material@sha256:11d7ec0a6e543bd56469a08d6ea1a7bc8c613cf6197be9629c4523d2d7db1c9c
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
