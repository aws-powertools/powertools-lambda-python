# v9.1.18
FROM squidfunk/mkdocs-material@sha256:b757834941211d24b913d75c32874a3678df0a4554f919b782943192dcd5104e
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
