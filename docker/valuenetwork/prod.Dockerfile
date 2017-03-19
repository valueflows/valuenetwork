# UNTESTED production image- placed for documenting differences from development image only!
FROM python:2.7
ENV PYTHONUNBUFFERED 1

RUN apt-get -yq install libjpeg-dev zlib1g-dev

RUN pip install -U setuptools

# copy all source files into the image
# (note: path is relative to build context specified in docker-compose.yaml, not Dockerfile)
COPY ./ /var/www/valuenetwork
WORKDIR /var/www/valuenetwork

# install required packages
RUN pip install -r requirements.txt --trusted-host dist.pinaxproject.com

# run migrations
RUN ./docker/valuenetwork/run-db-migrations.sh

EXPOSE 8000

CMD ["./manage.py", "runserver", "0.0.0.0:8000"]
