import requests, json, time, hashlib, hmac
from random import randint
from base64 import b64encode, b64decode
import logging

from django.conf import settings

class ChipChapAuthError(Exception):
    def __init__(self, message, errors):
        super(ChipChapAuthError, self).__init__(message)
        self.errors = errors

class ChipChapAuthConnection(object):

    def __init__(self):
        self.logger = self.init_logger()
        if 'client_id' in settings.MULTICURRENCY:
            self.able_to_connect = True
            cdata = settings.MULTICURRENCY
            self.client_id = cdata['client_id']
            self.client_secret = cdata['client_secret']
            self.access_key = cdata['access_key']
            self.access_secret = cdata['access_secret']
            self.url_client = cdata['url_client']
            self.url_history = cdata['url_history']
            self.url_balance = cdata['url_balance']
        else:
            self.able_to_connect = False
            self.logger.critical("Invalid configuration data to connect.")

    @classmethod
    def get(cls):
        return cls()

    @classmethod
    def init_logger(cls):
        logger = logging.getLogger("multicurrency")
        logger.setLevel(logging.WARNING)
        fhpath = "/".join([settings.PROJECT_ROOT, "multicurrency/multicurrency.log",])
        fh = logging.handlers.TimedRotatingFileHandler(fhpath, when="d", interval=1, backupCount=7)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    @classmethod
    def chipchap_x_signature(cls, access_key, access_secret):
        if len(access_secret) % 4:
            access_secret += '=' * (4 - len(access_secret) % 4)
        nonce = str(randint(0, 100000000))
        timestamp = str(int(time.time()))
        string_to_sign = access_key + nonce + timestamp
        signature = hmac.new(b64decode(access_secret), string_to_sign,
            digestmod=hashlib.sha256).hexdigest()
        headers = {'X-Signature':
            'Signature access-key="' + access_key +
            '", nonce="' + nonce +
            '", timestamp="' + timestamp +
            '", version="2", signature="' + signature +
            '"'}
        return headers

    def new_client(self, username, password):
        if not self.able_to_connect:
            raise ChipChapAuthError('Connection Error', 'No data to connect')

        headers = ChipChapAuthConnection.chipchap_x_signature(self.access_key, self.access_secret)
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': username,
            'password': password,
        }
        response = requests.post(self.url_client, headers=headers, data=data)
        if int(response.status_code) == 200:
            return response.json()
        else:
            self.logger.critical("Authentication request for " + username + " has returned "
                + str(response.status_code) + " status code. Error: " + response.text)
            raise ChipChapAuthError('Error ' + str(response.status_code), response.text)

    def wallet_history(self, access_key, access_secret, limit=10, offset=0):
        if not self.able_to_connect:
            raise ChipChapAuthError('Connection Error', 'No data to connect')

        headers = ChipChapAuthConnection.chipchap_x_signature(access_key, access_secret)
        params = {
            "limit": limit,
            "offset": offset,
        }
        tx_list = requests.get(self.url_history, headers=headers, params=params)
        balance = requests.get(self.url_balance, headers=headers)
        if int(tx_list.status_code) == 200 and int(balance.status_code) == 200:
            return tx_list.json(), balance.json()
        else:
            error = str(balance.status_code) + ' and ' + str(tx_list.status_code)
            msg = balance.text + ' and ' + tx_list.text
            self.logger.critical("History and balance request has returned "
                + error + " status codes. Error: " + msg)
            raise ChipChapAuthError('Error ' + error, msg)
