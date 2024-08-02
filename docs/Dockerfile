# v9.1.18
FROM squidfunk/mkdocs-material@sha256:9919d6ee948705ce6cd05e5bc0848af47de4f037afd7c3b91e776e7b119618a4
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
