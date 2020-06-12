FROM gitpod/workspace-full:latest

USER gitpod

RUN pip install --upgrade pip setupools poetry
