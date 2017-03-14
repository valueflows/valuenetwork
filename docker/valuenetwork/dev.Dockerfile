FROM python:2.7
ENV PYTHONUNBUFFERED 1

RUN apt-get -yq install libjpeg-dev zlib1g-dev

RUN pip install -U setuptools

# copy only the requirements file for getting dependencies preinstalled
# (note: path is relative to build context specified in docker-compose.yaml, not Dockerfile)
RUN mkdir -p /var/www/valuenetwork
COPY ./requirements.txt /var/www/valuenetwork
WORKDIR /var/www/valuenetwork

# install required packages into the container OS
RUN pip install -r requirements.txt --trusted-host dist.pinaxproject.com

# :NOTE: you will need to manually run migrations and setup a superadmin user yourself for development, see install_docker.txt

EXPOSE 8000

VOLUME /var/www/valuenetwork

CMD ["./manage.py", "runserver", "0.0.0.0:8000"]
