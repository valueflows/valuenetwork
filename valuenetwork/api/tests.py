"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class EconomicAgentSchemaTest(TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        os.environ['DJANGO_SETTINGS_MODULE'] = 'valuenetwork.settings'
        super(EconomicAgentSchemaTest, cls).setUpClass()
        import django
        django.setup()

    def setUp(self):
        from django.contrib.auth.models import User
        from valuenetwork.valueaccounting.models import EconomicAgent
        test_user, _ = User.objects.get_or_create(username='testUser11222')
        test_user.set_password('123456')
        test_user.save()
        test_agent, _ = EconomicAgent.objects.get_or_create(nick='testUser11222', agent_type_id=1)
        test_agent.name = 'testUser11222'
        if test_user not in test_agent.users.all():
            from valuenetwork.valueaccounting.models import AgentUser
            agent_user, _ = AgentUser.objects.get_or_create(agent=test_agent, user=test_user)
            test_agent.users.add(agent_user)
        test_agent.save()

    def test_basic_me_query(self):
        from .schema import schema

        result = schema.execute('''
        mutation {
          createToken(input: { username: "testUser11222", password: "123456" }) {
            token
            ok
            error
          }
        }
        ''')
        call_result = result.data['createToken']
        self.assertTrue(call_result['ok'], call_result['error'])
        token = call_result['token']
        query = '''
        query {
          viewer(token: "''' + token + '''") {
            agent(me: true) {
              name
            }
          }
        }
        '''
        result = schema.execute(query)
        self.assertTrue(result.data['viewer']['agent']['name'])
