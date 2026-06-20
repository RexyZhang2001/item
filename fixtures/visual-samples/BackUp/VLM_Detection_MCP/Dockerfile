FROM python:3.10-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

COPY config.yaml detect_core.py hiagent_api.py stream_capture.py artifact_storage.py ./
COPY weights/ weights/

ENV MPLBACKEND=Agg
EXPOSE 8080

CMD ["uvicorn", "hiagent_api:app", "--host", "0.0.0.0", "--port", "8080"]
