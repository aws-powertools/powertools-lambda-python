# v9.1.18
FROM squidfunk/mkdocs-material@sha256:33076657e536b6b8439168296a193098aef3c4c88cc2cecd0736cd391b90e7fd
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
