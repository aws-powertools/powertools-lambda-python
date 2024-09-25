# v9.1.18
FROM squidfunk/mkdocs-material@sha256:08fbf586e0963725a58eec1ab067ab9b23b804601e0bc2ddb3ab85a2b1ceeb7f
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
