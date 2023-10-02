# v9.1.18
FROM squidfunk/mkdocs-material@sha256:cbfecae461533759a5b376ef7ee3ee65cf328536261d28ae35df944c96e06867
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
