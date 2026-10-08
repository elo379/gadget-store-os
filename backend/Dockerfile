FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY scripts ./scripts
COPY migrations ./migrations
COPY alembic.ini ./
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 appuser
USER appuser
EXPOSE 8000
CMD ["/app/scripts/start-api.sh"]
