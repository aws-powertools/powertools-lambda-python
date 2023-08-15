# v9.1.18
FROM squidfunk/mkdocs-material@sha256:cd3a522b3282071586552499611f71206db0aec145d4d53822bc6fde76792cf8
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
