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
        self.url_client = "https://api.chip-chap.com/oauth/v1/public"
        self.url_history = "https://api.chip-chap.com/user/v2/wallet/transactions"

    @classmethod
    def get(cls):
        return cls()

    def new_client(self, username, password):
        access_key = self.access_key
        access_secret_bin = b64decode(self.access_secret)
        nonce = str(randint(0, 100000000))
        timestamp = str(int(time.time()))
        string_to_sign = access_key + nonce + timestamp
        signature = hmac.new(access_secret_bin, string_to_sign,
            digestmod=hashlib.sha256).hexdigest()
        headers = {'X-Signature':
            'Signature access-key="' + access_key +
            '", nonce="' + nonce +
            '", timestamp="' + timestamp +
            '", version="2", signature="' + signature +
            '"'}
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': username,
            'password': password,
        }
        response = requests.post(self.url_client, headers=headers, data=data)
        if response.status_code == '200' or response.status_code == 200:
            return response.json()
        else:
            raise FairpayOauth2Error('Error ' + str(response.status_code), response.text)

    def wallet_history(self, access_key, access_secret, limit=10, offset=0):
        if len(access_secret) % 4:
            access_secret += '=' * (4 - len(access_secret) % 4)

        nonce = str(randint(0, 100000000))
        timestamp = str(int(time.time()))
        string_to_sign = access_key + nonce + timestamp
        signature = hmac.new(b64decode(access_secret), string_to_sign, digestmod=hashlib.sha256).hexdigest()
        headers = {'X-Signature':
            'Signature access-key="' + access_key +
            '", nonce="' + nonce +
            '", timestamp="' + timestamp +
            '", version="2", signature="' + signature +
            '"'}
        data = {
            "limit": limit,
            "offset": offset,
        }
        response = requests.get(self.url_history, headers=headers, data=data)
        if response.status_code == '200' or response.status_code == 200:
            return response.json()
        else:
            raise FairpayOauth2Error('Error ' + str(response.status_code), response.text)

    def fake_wallet_history(self, access_key, access_secret, limit=10, offset=0):
        response = ('{"data":{"total":1,"start":0,"end":1,"daily":[],"scales":[],'
        '"elements":[{"created":"2017-05-11T17:27:46+0200","updated":"2017-05-11T17:48:08+0200",'
        '"id":"591482f314227e6d648b4567","group":211,"service":"fac-halcash_es","ip":"1.2.3.4",'
        '"status":"expired","version":1,"data_in":{"amount":"15000","phone":"666666666",'
        '"prefix":"34","concept":"webApp swift transaction","find_token":"5prgt4","pin":1234,'
        '"final":false,"status":false},"data_out":{"amount":295050734911,"currency":"FAC",'
        '"scale":8,"address":"fVFBKT5HKwgmqWY2rqxKxaPjuupJwH9LCS","expires_in":1200,'
        '"received":0,"min_confirmations":1,"confirmations":0,"status":"created","final":false},'
        '"currency":"EUR","amount":15000,"variable_fee":0,"fixed_fee":0,"total":15000,'
        '"scale":2,"notified":false,"pay_in_info":{"amount":295050734911,"currency":"FAC",'
        '"scale":8,"address":"fVFBKT5HKwgmqWY2rqxKxaPjuupJwH9LCS","expires_in":1200,"received":0,'
        '"min_confirmations":1,"confirmations":0,"status":"expired","final":false},'
        '"pay_out_info":{"amount":"15000","phone":"777777777","prefix":"34","concept":"webApp swift transaction",'
        '"find_token":"5prgt4","pin":4321,"final":false,"status":false},"method_in":"fac",'
        '"method_out":"halcash_es","type":"swift","price":5,"client":40,"client_data":[],'
        '"group_data":"","email_notification":""}]},"status":"ok","message":"Request successful"}')
        return json.loads(response)
