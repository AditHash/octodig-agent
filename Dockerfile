FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.21
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
COPY README.md ./
RUN groupadd --gid 10001 octodig && useradd --uid 10001 --gid octodig --no-create-home octodig
USER 10001:10001

EXPOSE 8000
CMD ["uvicorn", "octodig.api:app", "--host", "0.0.0.0", "--port", "8000"]
