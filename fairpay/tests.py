from __future__ import unicode_literals
from mock import patch
import json

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from fairpay.models import FairpayOauth2
from fairpay.utils import FairpayOauth2Connection, FairpayOauth2Error
from valuenetwork.valueaccounting.models import AgentType, EconomicAgent, AgentUser


def create_user_agent():
    individual_at, c = AgentType.objects.get_or_create(
        name='Individual', party_type='individual', is_context=False)
    test_agent, c = EconomicAgent.objects.get_or_create(name='test_agent',
        nick='test_agent', agent_type=individual_at,  is_context=False)
    test_user, c = User.objects.get_or_create(
        username = 'test_user',
        password = 'test_user_passwd',
        email = 'test_user@example.com',
    )
    AgentUser.objects.get_or_create(agent=test_agent, user=test_user)
    return test_agent

def fake_new_client(username, password):
    if username == 'fairpay_user' and password == 'fairpay_user_passwd':
        response = {
            'username': username,
            'access_key': 'TestAccessKey',
            'access_secret': 'TestAccessSecret'
        }
        return response
    else:
        raise FairpayOauth2Error('Error Testing', 'Authentication failed.')

def fake_wallet_history(access_key, access_secret):
    if access_key == 'TestAccessKey' and access_secret == 'TestAccessSecret':
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
    else:
        raise FairpayOauth2Error('Error Testing', 'Receiving transaction list failed.')

class FairpayOauth2Test(TestCase):

    def setUp(self):
        self.client = Client()
        self.agent = create_user_agent()

    @patch.object(FairpayOauth2Connection, 'new_client', fake_new_client)
    @patch.object(FairpayOauth2Connection, 'wallet_history', fake_wallet_history)
    def test_create_fairpayoauth2(self):
        self.client.login(username='test_user', password='test_user_passwd')

        url = reverse('fairpay_auth', args=[self.agent.id])
        data = {
            "name": "fairpay_user",
            "password": "fairpay_user_passwd",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        #url = reverse('fairpay_history', args=[self.agent.id, 1])
        #response = self.client.get(url)
        #self.assertEqual(response.status_code, 200)
