from django.test import TestCase


class AgentSchemaTest(TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        os.environ['DJANGO_SETTINGS_MODULE'] = 'valuenetwork.settings'
        super(AgentSchemaTest, cls).setUpClass()
        import django
        django.setup()

    def setUp(self):
        from django.contrib.auth.models import User
        from valuenetwork.valueaccounting.models import EconomicAgent, AgentAssociation, AgentType
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
          createToken(username: "testUser11222", password: "123456") {
            token
          }
        }
        ''')
        call_result = result.data['createToken']
        token = call_result['token']
        query = '''
        query {
          viewer(token: "''' + token + '''") {
            myAgent {
              name
            }
          }
        }
        '''
        result = schema.execute(query)
        self.assertEqual('testUser11222', result.data['viewer']['myAgent']['name'])

    def test_change_password(self):
        from .schema import schema

        result = schema.execute('''
                mutation {
                  createToken(username: "testUser11222", password: "123456") {
                    token
                  }
                }
                ''')
        call_result = result.data['createToken']
        token = call_result['token']
        from django.contrib.auth.models import User
        user = User.objects.get_by_natural_key('testUser11222')
        user.set_password('654321')
        user.save()
        query = '''
                query {
                  viewer(token: "''' + token + '''") {
                    myAgent {
                      name
                    }
                  }
                }
                '''
        result = schema.execute(query)
        self.assertEqual(None, result.data['viewer'])
        self.assertTrue(len(result.errors) == 1)
        self.assertEqual('Invalid password', str(result.errors[0]))

'''
query($token: String) {
  viewer(token: $token) {
    myAgent { 
      id 
      name
      image
      note
      type
    }
  }
} 
query($token: String) {
  viewer(token: $token) {
    agent(id:39) { 
      id 
      name
      image
      note
      type
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    allAgents { 
      id 
      name
      image
      note
      type
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    myOrganizations { 
      id 
      name
      image
      note
      type
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    allAgentRelationshipRoles { 
      id
      label
      inverseLabel
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    allAgentRelationships { 
      id
      subject
      relationship
      object
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    organizationMembers (id: 39) { 
      id 
      name
      image
      note
      type
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    agentRelationships (id: 39) { 
      id
      subject
      relationship
      object
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    economicResource(id: 26) {
      id
      resourceType
      trackingIdentifier
      image
      note
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    allEconomicResources {
      id
      resourceType
      trackingIdentifier
      image
      note
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    ownedEconomicResources (id: 26) {
      id
      resourceType
      trackingIdentifier
      image
      note
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    ownedCurrencyEconomicResources (id: 26) {
      id
      resourceType
      trackingIdentifier
      image
      note
    }
  }
}
query($token: String) {
  viewer(token: $token) {
    ownedInventoryEconomicResources (id: 26) {
      id
      resourceType
      trackingIdentifier
      image
      note
    }
  }
}
'''