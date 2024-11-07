FROM python:3.12-slim

WORKDIR /app

COPY dataportal-api/requirements.txt /app/
RUN pip install -r requirements.txt

COPY dataportal-api/dataportal /app/dataportal
COPY dataportal-api/manage.py /app/

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
