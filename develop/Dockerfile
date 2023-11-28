# v9.1.18
FROM squidfunk/mkdocs-material@sha256:8c72011a1da19cb96578eb8e3d8a24457a7891281202073c1a27aba51ef47b70
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
