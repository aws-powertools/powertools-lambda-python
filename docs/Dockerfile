# v9.1.18
FROM squidfunk/mkdocs-material@sha256:48d1914439e935734b9b0886c9d82da37d804d8f7a42cf2aedf090b054de2928
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
