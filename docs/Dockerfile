# v9.1.18
FROM squidfunk/mkdocs-material@sha256:e5f28aa0c3ac8206f93e44a0c52ea85616b0d6c674319cd1d87a241594788355
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
