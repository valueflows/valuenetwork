from django.test import TestCase, client_secret
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from fairpay.models import FairpayOauth2
from valueaccouting.models import AgentType, EconomicAgent, AgentUser


def create_user_agent(**kwargs):
    individual_at, c = AgentType.objects.get_or_create(
        name='Individual', party_type='individual', is_context=False)
    test_agent, c = EconomicAgent.objects.get_or_create(name='test_agent',
        nick='test_agent', agent_type=individual_at,  is_context=False)
    test_user, c = User.objects.get_or_create(
        username='test_user',
        password='test_user_passwd',
        email='test_user@example.com'
    )
    AgentUser.objects.get_or_create(agent=test_agent, user=test_user)
    return test_agent

class FairpayOauth2Test(TestCase):
    '''
    Tests for FairpayOauth2
    '''
    def setUp(self):
        self.client = Client()
        self.agent = create_user_agent()

    # TODO: mock API calls
    def test_create_fairpayoauth2(self):
        self.client.login(username='test_user', password='test_user_passwd')

        url = reverse('fairpay_auth', args=[self.agent.id])
        data = {
            "name" = "fairpay_user",
            "password" = "fairpay_user_passwd",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        url = reverse('fairpay_history', args=[self.agent.id])
        self.assertEqual(response.status_code, 200)
