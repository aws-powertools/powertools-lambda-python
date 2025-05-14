# v9.1.18
FROM squidfunk/mkdocs-material@sha256:eb04b60c566a8862be6b553157c16a92fbbfc45d71b7e4e8593526aecca63f52
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
