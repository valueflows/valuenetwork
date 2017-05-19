import requests, json, time, hashlib, hmac
from random import randint
from base64 import b64encode, b64decode
from django.conf import settings

class FairpayOauth2Error(Exception):
    def __init__(self, message, errors):
        super(FairpayOauth2Error, self).__init__(message)
        self.errors = errors

class FairpayOauth2Connection(object):

    def __init__(self):

        connecting_data = settings.FAIRPAY
        self.client_id = connecting_data['client_id']
        self.client_secret = connecting_data['client_secret']
        self.access_key = connecting_data['access_key']
        self.access_secret = connecting_data['access_secret']
        self.url_token = "https://api.chip-chap.com/oauth/v2/token"
        self.url_history = "https://api.chip-chap.com/user/v2/wallet/transactions"
        self.url_signature = "https://api.chip-chap.com/services/v1/echo"

    @classmethod
    def get(cls):
        return cls()

    def new_token(self, username, password):
        r = requests.post(self.url_token, data = {
            'grant_type':'password',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': username,
            'password': password,
        })
        if r.status_code == '200':
            return r.json()
        else:
            raise FairpayOauth2Error('Error ' + r.status_code, r.text)

    def wallet_history(self, access_token, limit=10, offset=0):
        headers = {"Authorization":"Bearer " + access_token}
        data = {
            "limit": limit,
            "offset": offset,
        }
        r = requests.get(self.url_history, headers=headers, data=data)
        if r.status_code == '200':
            return r.json()
        else:
            raise FairpayOauth2Error('Error ' + r.status_code, r.text)

    def signature_access(self):
        access_secret_bin = self.access_secret # b64decode(self.access_secret)
        nonce = str(randint(0, 100000000))
        timestamp = str(int(time.time()))
        string_to_sign = access_key + nonce + timestamp
        signature = b64encode(hmac.new(access_secret_bin, string_to_sign,
            digestmod=hashlib.sha256).digest())

        headers = {'X-Signature':
            'Signature access-key="' + access_key +
            '",nonce="' + nonce +
            '",timestamp="' + timestamp +
            '",version="1",signature="' + signature +
            '"'}

        r = requests.post(self.url_signature, headers = headers)
        if r.status_code == '200':
            return True
        else:
            raise FairpayOauth2Error('Error ' + r.status_code, r.text)
