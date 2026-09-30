FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

FROM python:3.13-slim AS runtime

LABEL org.opencontainers.image.title="Docker Hello App" \
      org.opencontainers.image.description="Простое веб-приложение на Python в Docker" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

ARG PORT=8000
ARG APP_VERSION=1.0.0

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=${PORT} \
    APP_VERSION=${APP_VERSION} \
    APP_NAME="Docker Hello App" \
    STATIC_DIR=/app/static

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/ /app/

RUN groupadd --system --gid 1001 appgroup \
 && useradd  --system --uid 1001 --gid appgroup \
             --home-dir /app --shell /usr/sbin/nologin appuser \
 && chown -R appuser:appgroup /app

USER appuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD ["python", "server.py", "--healthcheck"]

CMD ["python", "server.py"]
