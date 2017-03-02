FROM python:2.7
ENV PYTHONUNBUFFERED 1

RUN apt-get -yq install libjpeg-dev zlib1g-dev

RUN pip install -U setuptools

COPY . /var/www/valuenetwork

WORKDIR /var/www/valuenetwork

RUN pip install -r requirements.txt --trusted-host dist.pinaxproject.com

RUN ./manage.py migrate

# RUN ./manage.py createsuperuser

# These scripts do the same as createsuperuser, but non-interactively
COPY ./cmd/create-user.sh /usr/local/bin/create-user.sh
RUN chmod +x /usr/local/bin/create-user.sh
RUN /usr/local/bin/create-user.sh

# :TODO: fix test fixtures
# RUN ./manage.py loaddata ./fixtures/starters.json
# RUN ./manage.py loaddata ./fixtures/help.json
# RUN ./manage.py test valuenetwork.valueaccounting.tests

RUN /bin/bash -c 'cp valuenetwork/local_settings{_development,}.py'

EXPOSE 8000

VOLUME /var/www/valuenetwork

CMD ["./manage.py", "runserver"]
