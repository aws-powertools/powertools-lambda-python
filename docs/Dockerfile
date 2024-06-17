# v9.1.18
FROM squidfunk/mkdocs-material@sha256:257eca88da7f42242cd05e8cebf6d10ebd079edc207b089ad3f4f1ad107b0348
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
