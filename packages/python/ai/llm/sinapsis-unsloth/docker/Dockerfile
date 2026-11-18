FROM sinapsis-nvidia:base

COPY . /app/
WORKDIR /app
RUN uv sync --frozen

RUN uv pip install psutil setuptools torch ninja
RUN uv pip install sinapsis-unsloth[all] --extra-index-url https://pypi.sinapsis.tech
