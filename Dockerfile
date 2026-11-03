# Runtime image: the standard-library lab and nothing else, run as a non-root user.
FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    CONSENTDIFF_ENV=production CONSENTDIFF_HOST=0.0.0.0 CONSENTDIFF_PORT=8767 CONSENTDIFF_DATA_DIR=/data
RUN useradd --system --uid 10001 --no-create-home app && mkdir /data && chown app /data
WORKDIR /app
COPY consentdiff consentdiff
USER app
VOLUME /data
EXPOSE 8767
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ['CONSENTDIFF_PORT'], timeout=2)"]
CMD ["python", "-m", "consentdiff", "serve"]
