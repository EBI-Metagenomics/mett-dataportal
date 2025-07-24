FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY  dataportal_api/pyproject.toml  dataportal_api/uv.lock ./

# Install prod dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -r uv.lock --no-dev

# copy app
COPY dataportal_api/dataportal /app/dataportal
COPY dataportal_api/pyhmmer_search /app/pyhmmer_search
COPY dataportal_api/manage.py /app/

# Optional: collect static files
RUN mkdir -p /app/staticfiles
RUN python manage.py collectstatic --noinput --verbosity=2
RUN ls -la /app/staticfiles/ninja/ || echo "Static files not found"

# Final runtime image
FROM python:3.13-bookworm

WORKDIR /app

COPY --from=builder /app /app

# Set environment path (only if using .venv)
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers=4", "--access-logfile=-", "--log-file=-", "dataportal.wsgi"]
