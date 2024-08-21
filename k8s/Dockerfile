FROM python:3.12.4

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ADD manage.py /app/manage.py
ADD config/local.env /app/config/local.env
ADD dataportal /app/dataportal
ADD static /app/static
ADD templates /app/templates

# data migration -- hardcoding to be remvoed once database source is finalised
ADD data-generators /app/data-generators

WORKDIR /app

# migration step -- actual production will be different
RUN python manage.py migrate
RUN python manage.py import_data

# css generation step
RUN python manage.py compilescss
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "dataportal.wsgi"]