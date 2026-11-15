FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY ia/requirements.txt /tmp/ia_requirements.txt
RUN pip install --no-cache-dir -r /tmp/ia_requirements.txt

RUN pip install --no-cache-dir "ray[default]" fastapi uvicorn requests python-dotenv prometheus-client
