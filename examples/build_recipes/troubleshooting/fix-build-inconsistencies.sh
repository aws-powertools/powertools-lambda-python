#!/bin/bash
# 1. Use lock files for reproducible builds
# Poetry: poetry.lock
# uv: uv.lock
# pip: requirements.txt with pinned versions

# 2. Use Docker for consistent build environment
docker run --rm -v "$PWD":/app -w /app python:3.13-slim \
    bash -c "pip install -r requirements.txt -t build/"

# 3. Pin all tool versions
pip==24.0
poetry==1.8.0
uv==0.1.0

# 4. Use same Python version everywhere
python-version: '3.13'  # In CI/CD
python = "^3.13"        # In pyproject.toml
