FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the package and its dependencies first.
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install .

# Agent definitions and any runtime assets can be mounted through Compose
# rather than copied into the image.
#
# No CMD is defined intentionally. The same image is used by both the Router
# and API services, with their respective commands defined in compose.yaml.
