FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv export --format requirements-txt --no-hashes --no-dev | grep -v "^-e " > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN useradd --no-create-home appuser
USER appuser

ENV WEB_CONCURRENCY=4
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
