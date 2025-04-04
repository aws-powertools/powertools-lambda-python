# v9.1.18
FROM squidfunk/mkdocs-material@sha256:3555052d6cbde1086b166ebacacc43126c6fb0a7b990f324072150725aa63b18
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
