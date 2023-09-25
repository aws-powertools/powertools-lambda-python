# v9.1.18
FROM squidfunk/mkdocs-material@sha256:06673a1c5d556f1015ee0e71347060e58e280d6a25a7915d84c65a8ba6988610
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
