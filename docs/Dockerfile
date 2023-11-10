# v9.1.18
FROM squidfunk/mkdocs-material@sha256:f486dc932650bbbf71b83862715b842248973f1e240bf032c44ffe71906c40a4
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
