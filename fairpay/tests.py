from mock import patch

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

def fake_new_token(username, password):
    if username == 'fairpay_user' and password == 'fairpay_user_passwd':
        response = {
            'token_type': 'bearer',
            'expires_in': 3600,
            'scope': 'panel',
            'access_token': 'TestTokenTestTokenTestTokenTestTokenTestTokenTestTokenTestTokenTestTokenTestTokenTestT',
        }
        return response
    else:
        raise FairpayOauth2Error('Error Testing', 'Authentication failed.')

def fake_wallet_history(access_token):
    if access_token == 'TestTokenTestTokenTestTokenTestTokenTestTokenTestTokenTestTokenTestTokenTestTokenTestT':
        response = {} # TODO: return a coherent fake transactions list.
        return response
    else:
        raise FairpayOauth2Error('Error Testing', 'Receiving transaction list failed.')

class FairpayOauth2Test(TestCase):

    def setUp(self):
        self.client = Client()
        self.agent = create_user_agent()

    @patch.object(FairpayOauth2Connection, 'new_token', fake_new_token)
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

        # TODO: receive a coherent fake transaction list.
        #url = reverse('fairpay_history', args=[self.agent.id])
        #self.assertEqual(response.status_code, 200)
