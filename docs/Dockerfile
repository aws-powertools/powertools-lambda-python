# v9.1.18
FROM squidfunk/mkdocs-material@sha256:c4890abf881d379f57b058ff2a387ab75a30f63194ddd004420ed3341e98fe9f
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
