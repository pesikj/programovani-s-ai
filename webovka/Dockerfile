FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-cache

COPY . .
# Jen pro collectstatic; skutečné hodnoty se předávají až při spuštění.
RUN DJANGO_SECRET_KEY=build-only-not-a-runtime-secret \
    POSTGRES_DB=build POSTGRES_USER=build POSTGRES_PASSWORD=build \
    POSTGRES_HOST=db python manage.py collectstatic --noinput

RUN useradd --uid 10001 --create-home app
USER app
EXPOSE 8000

CMD ["sh", "/app/entrypoint.sh"]
