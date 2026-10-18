# Local docs preview with Zensical (see `make docs-local-docker`)
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt
WORKDIR /docs
EXPOSE 8000
ENTRYPOINT ["zensical"]
CMD ["serve", "--dev-addr", "0.0.0.0:8000"]
