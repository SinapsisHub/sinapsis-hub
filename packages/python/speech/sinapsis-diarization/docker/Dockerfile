FROM sinapsis-nvidia:base

RUN apt-get update && apt-get install -y git && apt-get clean

COPY . /app/
WORKDIR /app
RUN uv sync --frozen
RUN uv pip install sinapsis-diarization[all] --extra-index-url https://pypi.sinapsis.tech
RUN uv pip install "cuda-bindings>=13.0.0"
