# v9.1.18
FROM squidfunk/mkdocs-material@sha256:49d1bfdaf457c5ac20a93ff59a5b57b762ace5606fc564ac2e195abf315f14ee
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
