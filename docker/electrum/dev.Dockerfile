FROM python:2.7
ENV PYTHONUNBUFFERED 1

RUN pip install -U setuptools

RUN pip install https://electrum.fair-coin.org/download/Electrum-fair-2.3.3.tar.gz
RUN pip install jsonrpclib

VOLUME /root/.electrum-fair/wallets

COPY ./docker/electrum/run-or-wait-for-setup.sh /root/.electrum-fair/run-or-wait-for-setup.sh

CMD ["/root/.electrum-fair/run-or-wait-for-setup.sh"]
