########## build stage ##########
FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential libffi-dev cargo && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app/server
COPY requirements.txt .
COPY server/ ./server

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip wheel && \
    pip wheel --wheel-dir /wheels -r requirements.txt

RUN adduser --disabled-password --gecos "" openvimai
########## runtime stage ##########
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app/server
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/* && \
    rm -rf /root/.cache

COPY server/ ./server
RUN adduser --disabled-password --gecos "" openvimai && \
    chown -R openvimai:openvimai /app
USER openvimai

########## healthcheck ##########
HEALTHCHECK --interval=30s --timeout=3s CMD \
  curl -fs http://localhost:8000/health || exit 1

EXPOSE 8000

########## command (prod) ##########
CMD ["gunicorn", "server.main:app", "--workers", "1", \
     "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]

