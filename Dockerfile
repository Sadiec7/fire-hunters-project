FROM python:3.10-slim
RUN pip install --no-cache-dir "ray[default]" fastapi uvicorn requests numpy pandas pyarrow python-dotenv
WORKDIR /workspace