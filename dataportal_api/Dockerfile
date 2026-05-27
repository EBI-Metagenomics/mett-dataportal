FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY dataportal_api/pyproject.toml /app/
COPY dataportal_api/uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=dataportal_api/uv.lock,target=uv.lock \
    --mount=type=bind,source=dataportal_api/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# copy app selectively
COPY dataportal_api/dataportal /app/dataportal
COPY dataportal_api/pyhmmer_search /app/pyhmmer_search
COPY dataportal_api/manage.py /app/


RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Optional: collect static files
RUN mkdir -p /app/staticfiles
RUN uv run python manage.py collectstatic --noinput --verbosity=2
RUN ls -la /app/staticfiles/ninja/ || echo "Static files not found"

# Final runtime image
FROM python:3.13-slim AS runtime

RUN groupadd -r mett && useradd -r -g mett -u 10001 mett

WORKDIR /app

COPY --from=builder --chown=mett:mett /app /app

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

USER 10001

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers=4", "--access-logfile=-", "--log-file=-", "dataportal.wsgi"]
