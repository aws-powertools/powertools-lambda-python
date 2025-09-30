# v9.1.18
FROM squidfunk/mkdocs-material@sha256:00f9276315990b82f5af8c47bb2b71e2c69aef9f02a08f8dffd2515f42310753
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
