# v9.1.18
FROM squidfunk/mkdocs-material@sha256:405aeb6dbf1fcddd1082993eacf288a46648ea56b846323f001aee619015a23b
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
