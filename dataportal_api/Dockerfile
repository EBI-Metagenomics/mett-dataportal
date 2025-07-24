FROM python:3.13-slim

WORKDIR /app

COPY dataportal_api/requirements.txt /app/
RUN pip install -r requirements.txt

COPY dataportal_api/dataportal /app/dataportal
COPY dataportal_api/pyhmmer_search /app/pyhmmer_search
COPY dataportal_api/manage.py /app/

# Create static directory and collect static files
RUN mkdir -p /app/staticfiles
RUN python manage.py collectstatic --noinput --verbosity=2
RUN ls -la /app/staticfiles/ninja/ || echo "Static files not found"

# Optional: precompile Celery app to speed up container start
# RUN python -m compileall /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "dataportal.wsgi:application"]
