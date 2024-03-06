# v9.1.18
FROM squidfunk/mkdocs-material@sha256:3678304a65e17660953a30c0a0be0bc2fb8f55ac450216c14af6ba942badc4dc
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
