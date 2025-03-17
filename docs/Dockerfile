# v9.1.18
FROM squidfunk/mkdocs-material@sha256:479a06a8f5a320a9b2b17e72cb7012388d66ea71a8568235cfa072eb152bc30c
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
