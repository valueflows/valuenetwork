from django.test import TestCase
from django.contrib.auth.models import User
from valuenetwork.valueaccounting.models import *
from valuenetwork.api.models import *
from .schema import schema


class APITest(TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        os.environ['DJANGO_SETTINGS_MODULE'] = 'valuenetwork.settings'
        super(APITest, cls).setUpClass()
        import django
        django.setup()

    def setUp(self):
        # agent data
        at_person = AgentType.objects.get(name="Individual")
        at_org = AgentType.objects.get(name="Organization")
        aat_member = AgentAssociationType.objects.get(identifier="member")
        aat_supplier = AgentAssociationType.objects.get(identifier="supplier")
        test_user, _ = User.objects.get_or_create(username='testUser11222')
        test_user.set_password('123456')
        test_user.save()
        test_agent, _ = EconomicAgent.objects.get_or_create(nick='testUser11222', agent_type=at_person)
        test_agent.name = 'testUser11222'
        if test_user not in test_agent.users.all():
            from valuenetwork.valueaccounting.models import AgentUser
            agent_user, _ = AgentUser.objects.get_or_create(agent=test_agent, user=test_user)
            test_agent.users.add(agent_user)
        test_agent.save()
        org1 = EconomicAgent(
            name="org1",
            nick="org1",
            agent_type=at_org,
            )
        org1.save()
        org2 = EconomicAgent(
            name="org2",
            nick="org2",
            agent_type=at_org,
            )
        org2.save()
        another_person = EconomicAgent(
            name="not user",
            nick="not user",
            agent_type=at_person,
            )
        another_person.save()
        supplier = EconomicAgent(
            name="supp1",
            nick="supp1",
            agent_type=at_org,
            )
        supplier.save()
        test_agent_org1 = AgentAssociation(
            is_associate=test_agent,
            has_associate=org1,
            association_type=aat_member,
            )
        test_agent_org1.save()
        another_person_org1 = AgentAssociation(
            is_associate=another_person,
            has_associate=org1,
            association_type=aat_member,
            )
        another_person_org1.save()
        test_agent_org2 = AgentAssociation(
            is_associate=test_agent,
            has_associate=org2,
            association_type=aat_member,
            )
        test_agent_org2.save()
        supplier_org1 = AgentAssociation(
            is_associate=supplier,
            has_associate=org1,
            association_type=aat_supplier,
            )
        supplier_org1.save()

        # resource data
        unit_each = Unit(
            unit_type = "quantity",
            abbrev = "EA",
            name = "Each",
            )
        unit_each.save()
        unit_hours = Unit(
            unit_type = "time",
            abbrev = "HR",
            name = "Hours",
            )
        unit_hours.save()
        rti1 = EconomicResourceType(
            name='component1',
            unit=unit_each,
            behavior="consumed",
            inventory_rule="yes",
            )
        rti1.save()
        rti3 = EconomicResourceType(
            name='product1',
            unit=unit_each,
            behavior="produced",
            inventory_rule="yes",
            )
        rti3.save()
        rti2 = EconomicResourceType(
            name='work1',
            unit=unit_hours,
            behavior="work",
            inventory_rule="never",
            )
        rti2.save()
        res1 = EconomicResource(
            resource_type=rti1,
            identifier="a-component",
            quantity=5,
            )
        res1.save()
        res2 = EconomicResource(
            resource_type=rti1,
            identifier="another-component",
            quantity=100,
            )
        res2.save()
        res3 = EconomicResource(
            resource_type=rti1,
            identifier="a-product",
            quantity=10,
            )
        res3.save()

    def test_basic_me_query(self):

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

        result = schema.execute('''
                mutation {
                  createToken(username: "testUser11222", password: "123456") {
                    token
                  }
                }
                ''')
        call_result = result.data['createToken']
        token = call_result['token']
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

    def test_single_agent(self):
        result = schema.execute('''
                mutation {
                  createToken(username: "testUser11222", password: "123456") {
                    token
                  }
                }
                ''')
        call_result = result.data['createToken']
        token = call_result['token']
        test_agent = EconomicAgent.objects.get(name="testUser11222")

        query = '''
                query {
                  viewer(token: "''' + token + '''") {
                    agent(id:''' + str(test_agent.id) + ''') {
                      name
                    }
                  }
                }
                '''
        result = schema.execute(query)
        self.assertEqual('testUser11222', result.data['viewer']['agent']['name'])

    def test_agents_and_relationships(self):
        result = schema.execute('''
                mutation {
                  createToken(username: "testUser11222", password: "123456") {
                    token
                  }
                }
                ''')
        call_result = result.data['createToken']
        token = call_result['token']
        test_agent = EconomicAgent.objects.get(name="testUser11222")

        query = '''
                query {
                  viewer(token: "''' + token + '''") {
                    allAgents {
                      name
                      type
                      __typename
                      members: agentRelationships(category: MEMBER) {
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
                      tps: agentRelationships(category: TRADINGPARTNER) {
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
                      agentRoles {
                          label
                          category
                      }
                    }
                  }
                }
                '''
        result = schema.execute(query)
        allAgents = result.data['viewer']['allAgents']
        self.assertEqual(len(allAgents), 5)
        org1 = allAgents[1]
        self.assertEqual(org1['name'], 'org1')
        agentRelationships = org1['tps']
        supplier = agentRelationships[0]
        self.assertEqual(supplier['subject']['name'], 'supp1')
        self.assertEqual(org1['__typename'], 'Organization')
        self.assertEqual(org1['type'], 'Organization')
        person = allAgents[0]
        self.assertEqual(person['__typename'], 'Person')
        roles = person['agentRoles']
        role = roles[0]
        self.assertEqual(role['label'], 'is member of')

    def test_resources_and_resource_types(self):
        result = schema.execute('''
                mutation {
                  createToken(username: "testUser11222", password: "123456") {
                    token
                  }
                }
                ''')
        call_result = result.data['createToken']
        token = call_result['token']
        test_agent = EconomicAgent.objects.get(name="testUser11222")

        query = '''
                query {
                  viewer(token: "''' + token + '''") {
                    resourceTaxonomyItemsByProcessCategory(category: CONSUMED) {
                      name
                      category
                      processCategory
                      taxonomyItemResources {
                        trackingIdentifier
                        currentQuantity {
                          numericValue
                          unit {
                            name
                          }
                        }
                        resourceTaxonomyItem {
                          name
                        }
                        image
                        category
                        note
                      }
                    }
                    resourceTaxonomyItemsByAction(action: PRODUCE) {
                      name
                      category
                      processCategory
                      taxonomyItemResources {
                        trackingIdentifier
                      }
                    }
                  }
                }
                '''
        result = schema.execute(query)
        resourceTaxonomyItemsByProcessCategory = result.data['viewer']['resourceTaxonomyItemsByProcessCategory']
        resourceTaxonomyItemsByAction = result.data['viewer']['resourceTaxonomyItemsByAction']
        #import pdb; pdb.set_trace()
        self.assertEqual(len(resourceTaxonomyItemsByProcessCategory), 1)
        rti1 = resourceTaxonomyItemsByProcessCategory[0]
        self.assertEqual(rti1['name'], 'component1')
        consumed_resources = rti1['taxonomyItemResources']
        self.assertEqual(len(consumed_resources), 3)
        conres1 = consumed_resources[0]
        self.assertEqual(conres1['trackingIdentifier'], 'a-component')
        prod_resources = resourceTaxonomyItemsByAction[0]['taxonomyItemResources']
        prodres1 = prod_resources[1]
        self.assertEqual(prodres1['trackingIdentifier'], 'a-product')



######################### SAMPLE QUERIES #####################

'''
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
    fcOrganizations (visibility:"public", joiningStyle:"moderated") {
      id
      name
      image
      type
    }
  }
}

query($token: String) {
  viewer(token: $token) {
    organizationTypes {
      name
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

query ($token: String) {
  viewer(token: $token) {
    resourceTaxonomyItem(id: 31) {
      name
      taxonomyItemResources {
        trackingIdentifier
        currentQuantity {
          numericValue
          unit {
            name
          }
        }
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    resourceTaxonomyItemsByProcessCategory(category: CONSUMED) {
      name
      category
      processCategory
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    resourceTaxonomyItemsByAction(action: PRODUCE) {
      name
      category
      processCategory
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
fragment coreCommitmentFields on Commitment {
  action
  commitmentStart
  committedOn
  due
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
}
query ($token: String) {
  viewer(token: $token) {
    process(id: 6) {
      name
      processEconomicEvents {
        ...coreEventFields
      }
      processCommitments {
        ...coreCommitmentFields
      }
      inputs {
        ...coreEventFields
      }
      workInputs {
        ...coreEventFields
      }
      nonWorkInputs {
        ...coreEventFields
      }
      outputs {
        ...coreEventFields
      }
      committedInputs {
        ...coreCommitmentFields
      }
      committedWorkInputs {
        ...coreCommitmentFields
      }
      committedNonWorkInputs {
        ...coreCommitmentFields
      }
      committedOutputs {
        ...coreCommitmentFields
      }
      nextProcesses {
        name
      }
      previousProcesses {
        name
      }
    }
  }
}

query ($token: String) {
  viewer(token: $token) {
    process(id: 52) {
      name
      isStarted
      isFinished
      workingAgents {
        name
        image
        __typename
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
        commitmentStart
        committedOn
        due
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
      commitmentStart
      committedOn
      due
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
      commitmentStart
      committedOn
      due
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
