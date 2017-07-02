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
# test queries, full coverage

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
      __typename
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    person(id:6) {
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
    allPeople {
      id
      name
      image
      note
      type
      __typename
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    organization(id:26) {
      id
      name
      image
      note
      type
      __typename
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    allOrganizations {
      id
      name
      image
      note
      type
      __typename
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

fragment coreAgentFields on Agent {
  id
  name
  image
  note
  type
}
query ($token: String) {
  viewer(token: $token) {
    myAgent {
      ...coreAgentFields
      memberOfOrganizations {
        id
        name
        members {
          name
          memberOfOrganizations {
            name
          }
        }
      }
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    allAgentRelationshipRoles {
      id
      label
      inverseLabel
      category
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    agentRelationship(id:20) {
      subject {
        name
        type
      }
      relationship {
        label
        category
      }
      object {
        name
        type
      }
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    allAgentRelationships {
      id
      subject {
        name
        type
      }
      relationship {
        label
        category
      }
      object {
        name
        type
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    agent(id: 39) {
      name
      agentRelationships {
        id
        subject {
          name
          type
        }
        relationship {
          label
          category
        }
        object {
          name
          type
        }
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    agent(id: 39) {
      name
      agentRelationships(category: MEMBER) {
        id
        subject {
          name
          type
        }
        relationship {
          label
          category
        }
        object {
          name
          type
        }
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    agent(id: 39) {
      name
      agentRelationships(roleId: 2) {
        id
        subject {
          name
          type
        }
        relationship {
          label
          category
        }
        object {
          name
          type
        }
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    agent(id: 39) {
      name
      agentRoles {
        label
        category
      }
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    unit(id:8) {
      id
      name
      symbol
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    allUnits {
      id
      name
      symbol
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    resourceTaxonomyItem(id:38) {
      id
      name
      image
      category
      note
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    allResourceTaxonomyItems {
      id
      name
      image
      category
      note
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    economicResource(id: 26) {
      id
      resourceTaxonomyItem {
        name
        category
      }
      trackingIdentifier
      currentQuantity {
        numericValue
        unit {
          name
        }
      }
      image
      category
      note
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    allEconomicResources {
      id
      resourceTaxonomyItem {
        name
        category
      }
      trackingIdentifier
      currentQuantity {
        numericValue
        unit {
          name
        }
      }
      image
      note
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    agent(id: 26) {
      name
      ownedEconomicResources {
        id
        resourceTaxonomyItem {
          name
          category
        }
        trackingIdentifier
        currentQuantity {
          numericValue
          unit {
            name
          }
        }
        image
        note
        category
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    agent(id: 6) {
      name
      ownedEconomicResources(category: CURRENCY) {
        id
        resourceTaxonomyItem {
          name
          category
        }
        trackingIdentifier
        currentQuantity {
          numericValue
          unit {
            name
          }
        }
        image
        note
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    agent(id: 26) {
      name
      ownedEconomicResources(category: INVENTORY) {
        id
        resourceTaxonomyItem {
          name
          category
        }
        trackingIdentifier
        currentQuantity {
          numericValue
          unit {
            name
          }
        }
        image
        note
      }
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    process(id:3) {
      id
      name
      plannedStart
      plannedDuration
      isFinished
      note
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    allProcesses {
      id
      name
      plannedStart
      plannedDuration
      isFinished
      note
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    agent(id:26) {
      name
      agentProcesses {
        id
        name
        plannedStart
        plannedDuration
        isFinished
        note
      }
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    agent(id:26) {
      name
      agentProcesses (isFinished: false) {
        id
        name
        plannedStart
        plannedDuration
        isFinished
        note
      }
    }
  }
}

fragment coreEventFields on EconomicEvent {
  action
  start
  affectedQuantity {
    numericValue
    unit {
      name
    }
  }
  note
  affectedResource {
    id
    resourceTaxonomyItem {
      name
      category
    }
    trackingIdentifier
  }
  provider {
    id
    name
  }
  receiver {
    id
    name
  }
}
query ($token: String) {
  viewer(token: $token) {
    process(id: 6) {
      name
      inputs {
        ...coreEventFields
      }
      outputs {
        ...coreEventFields
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    allEconomicEvents {
      id
      action
      start
      affectedQuantity {
        numericValue
        unit {
          name
        }
      }
      note
      affectedResource {
        id
        resourceTaxonomyItem {
          name
          category
        }
        trackingIdentifier
      }
      provider {
        id
        name
      }
      receiver {
        id
        name
      }
      process {
        id
        name
      }
      scope {
        id
        name
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    agent(id: 6) {
      name
      agentEconomicEvents(latestNumberOfDays: 30) {
        id
        action
        start
        affectedQuantity {
          numericValue
          unit {
            name
          }
        }
        affectedResource {
          id
          resourceTaxonomyItem {
            name
            category
          }
          trackingIdentifier
        }
        provider {
          id
          name
        }
        receiver {
          id
          name
        }
        process {
          id
          name
        }
        note
      }
      agentCommitments(latestNumberOfDays: 30) {
        id
        action
        commitmentDate
        committedQuantity {
          numericValue
          unit {
            name
          }
        }
        committedTaxonomyItem {
          name
          category
        }
        provider {
          id
          name
        }
        receiver {
          id
          name
        }
        process {
          id
          name
        }
        note
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    economicEvent(id: 296) {
      id
      action
      start
      affectedQuantity {
        numericValue
        unit {
          name
        }
      }
      note
      affectedResource {
        id
        resourceTaxonomyItem {
          name
          category
        }
        trackingIdentifier
      }
      provider {
        id
        name
      }
      receiver {
        id
        name
      }
      process {
        id
        name
      }
      scope {
        id
        name
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    economicEvent(id: 316) {
      id
      action
      start
      affectedQuantity {
        numericValue
        unit {
          name
        }
      }
      note
      affectedResource {
        id
        resourceTaxonomyItem {
          name
          category
        }
        trackingIdentifier
      }
      provider {
        id
        name
      }
      receiver {
        id
        name
      }
      process {
        id
        name
      }
      scope {
        id
        name
      }
      fulfills {
        commitmentDate
        committedQuantity {
          numericValue
        }
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    allCommitments {
      id
      action
      committedStart
      committedQuantity {
        numericValue
        unit {
          name
        }
      }
      note
      committedTaxonomyItem {
        name
        category
      }
      committedResource {
        id
        resourceTaxonomyItem {
          name
          category
        }
        trackingIdentifier
      }
      provider {
        id
        name
      }
      receiver {
        id
        name
      }
      process {
        id
        name
      }
      scope {
        id
        name
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    commitment(id: 325) {
      id
      action
      commitmentDate
      committedStart
      committedQuantity {
        numericValue
        unit {
          name
        }
      }
      note
      committedTaxonomyItem {
        name
        category
      }
      committedResource {
        id
        resourceTaxonomyItem {
          name
          category
        }
        trackingIdentifier
      }
      provider {
        id
        name
      }
      receiver {
        id
        name
      }
      process {
        id
        name
      }
      scope {
        id
        name
      }
      fulfilledBy {
        action
        start
        provider {
          name
        }
      }
    }
  }
}

'''
