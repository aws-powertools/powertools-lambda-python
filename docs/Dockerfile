# Local docs preview with Zensical (see `make docs-local-docker`)
# python:3.12-slim
FROM python@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt
# Same UID as the typical host user, so files written to the mounted volume are not owned by root
RUN useradd --uid 1000 --create-home docs
USER docs
WORKDIR /docs
EXPOSE 8000
ENTRYPOINT ["zensical"]
CMD ["serve", "--dev-addr", "0.0.0.0:8000"]
