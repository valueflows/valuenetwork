FROM python:2.7
ENV PYTHONUNBUFFERED 1

RUN apt-get -yq install libjpeg-dev zlib1g-dev

RUN pip install -U setuptools

# we need sudo command installed (even though it's not necessary) for compatibility with some daemon scripts
RUN apt-get update && \
  apt-get -y install sudo

# install electrum libs first (needed by FairCoin daemon)
RUN pip install https://electrum.fair-coin.org/download/Electrum-fair-2.3.3.tar.gz

# copy only the requirements file for getting dependencies preinstalled
# (note: path is relative to build context specified in docker-compose.yaml, not Dockerfile)
RUN mkdir -p /var/www/valuenetwork
COPY ./requirements.txt /var/www/valuenetwork
WORKDIR /var/www/valuenetwork

# install required packages into the container OS
RUN pip install -r requirements.txt --trusted-host dist.pinaxproject.com

# :NOTE: you will need to manually run migrations and setup a superadmin user yourself for development, see install_docker.txt

EXPOSE 8000

# volume to mount the local app code into
VOLUME /var/www/valuenetwork
# volume to mount electrum wallet files in to share with the app
VOLUME /home/ocp/.electrum-fair/wallets/

CMD ["./docker/valuenetwork/run-all-services.sh"]
