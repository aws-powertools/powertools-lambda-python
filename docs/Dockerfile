# v9.1.18
FROM squidfunk/mkdocs-material@sha256:cb38dc2e1094228cad571eb0c9c6f0ec760adfa4c3e6112fda57e8b62ae18592
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
