FROM python:3.13-slim

WORKDIR /app

COPY dataportal_api/requirements.txt /app/
RUN pip install -r requirements.txt

COPY dataportal_api/dataportal /app/dataportal
COPY dataportal_api/pyhmmer_search /app/pyhmmer_search
COPY dataportal_api/manage.py /app/

# Collect static files
# RUN python manage.py collectstatic --noinput

# Optional: precompile Celery app to speed up container start
# RUN python -m compileall /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
