# v9.1.18
FROM squidfunk/mkdocs-material@sha256:df9409b9be06e6964c23013002169805de5910db9f53d916d6ce28fb1e9088cb
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
