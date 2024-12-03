FROM 3.12.7-bullseye

WORKDIR /app

COPY dataportal_api/requirements.txt /app/
RUN pip install -r requirements.txt

COPY dataportal_api/dataportal /app/dataportal
COPY dataportal_api/manage.py /app/

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
