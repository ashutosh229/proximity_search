# ---------- stage 1: dependencies ----------
FROM python:3.12-slim AS build
WORKDIR /w
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- stage 2: sample data (so `docker compose up` needs no pre-step) ----------
FROM python:3.12-slim AS data
WORKDIR /d
COPY scripts/generate_sample_data.py .
RUN python generate_sample_data.py --out /d/data

# ---------- stage 3: runtime ----------
FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DATA_DIR=/srv/data \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prom \
    WEB_CONCURRENCY=4
COPY --from=build /install /usr/local
RUN useradd -r -u 10001 app && mkdir -p /tmp/prom && chown app /tmp/prom
COPY app ./app
COPY scripts ./scripts
COPY --from=data /d/data ./data
USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/ready')" || exit 1
CMD ["sh", "-c", "rm -rf /tmp/prom/* && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --timeout-graceful-shutdown 20"]
