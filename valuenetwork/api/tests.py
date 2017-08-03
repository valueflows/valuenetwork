from django.test import TestCase
from django.contrib.auth.models import User
from valuenetwork.valueaccounting.models import *
from valuenetwork.api.models import *
from .schema import schema
import datetime

import logging
logger = logging.getLogger("graphql.execution.executor").addHandler(logging.NullHandler())
# Note: if you want to see the executor error messages,
# comment out the line above and uncomment the one below:
#logging.basicConfig()

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
            resource_type=rti3,
            identifier="a-product",
            quantity=20,
            )
        res3.save()
        arr1 = AgentResourceRoleType(
            name="owner",
            is_owner=True,
            )
        arr1.save()
        arr2 = AgentResourceRoleType(
            name="custodian",
            is_owner=False,
            )
        arr2.save()
        a1r3 = AgentResourceRole(
            agent=org1,
            resource=res3,
            role=arr1,
            )
        a1r3.save()
        a1r2 = AgentResourceRole(
            agent=org1,
            resource=res2,
            role=arr1,
            )
        a1r2.save()
        a1r1 = AgentResourceRole(
            agent=org1,
            resource=res1,
            role=arr2,
            )
        a1r1.save()

        # process-commitment-event data
        proc1 = Process(
            name="proc1",
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=5),
            finished=False,
            context_agent=org1,
            )
        proc1.save()
        proc2 = Process(
            name="proc2",
            start_date=datetime.date.today() - datetime.timedelta(days=5),
            end_date=datetime.date.today() - datetime.timedelta(days=2),
            finished=True,
            context_agent=org1,
            )
        proc2.save()
        proc3 = Process(
            name="proc3",
            start_date=datetime.date.today() + datetime.timedelta(days=10),
            end_date=datetime.date.today() + datetime.timedelta(days=15),
            finished=False,
            context_agent=org2,
            )
        proc3.save()
        et_cite = EventType.objects.get(name="Citation")
        et_produce = EventType.objects.get(name="Resource Production")
        et_todo = EventType.objects.get(name="Todo")
        et_use = EventType.objects.get(name="Resource use")
        et_work = EventType.objects.get(name="Time Contribution")
        et_tobechanged = EventType.objects.get(name="To Be Changed")
        et_change = EventType.objects.get(name="Change")
        et_consume = EventType.objects.get(name="Resource Consumption")
        proc1_c1 = Commitment(
            event_type=et_work,
            due_date=datetime.date.today() + datetime.timedelta(days=10),
            from_agent=test_agent,
            resource_type=rti2,
            process=proc1,
            context_agent=org1,
            quantity=3,
            unit_of_quantity=unit_hours,
            )
        proc1_c1.save()
        proc1_c2 = Commitment(
            event_type=et_work,
            due_date=datetime.date.today() + datetime.timedelta(days=10),
            from_agent=another_person,
            resource_type=rti2,
            process=proc1,
            context_agent=org1,
            quantity=2.5,
            unit_of_quantity=unit_hours,
            )
        proc1_c2.save()
        proc1_c3 = Commitment(
            event_type=et_consume,
            due_date=datetime.date.today() + datetime.timedelta(days=10),
            #from_agent=another_person,
            resource_type=rti1,
            process=proc1,
            context_agent=org1,
            quantity=3,
            unit_of_quantity=unit_each,
            )
        proc1_c3.save()
        proc1_c4 = Commitment(
            event_type=et_produce,
            due_date=datetime.date.today() + datetime.timedelta(days=10),
            #from_agent=another_person,
            resource_type=rti3,
            process=proc1,
            context_agent=org1,
            quantity=1,
            unit_of_quantity=unit_each,
            )
        proc1_c4.save()
        proc1_e1 = EconomicEvent(
            event_type=et_work,
            event_date=datetime.date.today(),
            from_agent=test_agent,
            resource_type=rti2,
            process=proc1,
            context_agent=org1,
            quantity=Decimal(1),
            unit_of_quantity=unit_hours,
            commitment=proc1_c1,
            )
        proc1_e1.save()
        proc1_e2 = EconomicEvent(
            event_type=et_work,
            event_date=datetime.date.today() + datetime.timedelta(days=1),
            from_agent=test_agent,
            resource_type=rti2,
            process=proc1,
            context_agent=org1,
            quantity=Decimal(1.5),
            unit_of_quantity=unit_hours,
            commitment=proc1_c1,
            )
        proc1_e2.save()
        proc1_e3 = EconomicEvent(
            event_type=et_work,
            event_date=datetime.date.today() + datetime.timedelta(days=1),
            from_agent=another_person,
            resource_type=rti2,
            process=proc1,
            context_agent=org1,
            quantity=Decimal(3),
            unit_of_quantity=unit_hours,
            commitment=proc1_c2,
            )
        proc1_e3.save()
        proc1_e4 = EconomicEvent(
            event_type=et_consume,
            event_date=datetime.date.today(),
            #from_agent=another_person,
            resource_type=rti1,
            resource=res1,
            process=proc1,
            context_agent=org1,
            quantity=Decimal(3),
            unit_of_quantity=unit_each,
            commitment=proc1_c3,
            )
        proc1_e4.save()
        proc1_e5 = EconomicEvent(
            event_type=et_produce,
            event_date=datetime.date.today() + datetime.timedelta(days=3),
            from_agent=org1,
            resource_type=rti3,
            resource=res3,
            process=proc1,
            context_agent=org1,
            quantity=Decimal(1),
            unit_of_quantity=unit_each,
            commitment=proc1_c4,
            )
        proc1_e5.save()
        proc1_e6 = EconomicEvent(
            event_type=et_produce,
            event_date=datetime.date.today() + datetime.timedelta(days=3),
            from_agent=org1,
            resource_type=rti1,
            resource=res2,
            process=proc1,
            context_agent=org1,
            quantity=Decimal(2),
            unit_of_quantity=unit_each,
            commitment=None,
            )
        proc1_e6.save()
        proc2_e1 = EconomicEvent(
            event_type=et_produce,
            event_date=datetime.date.today() - datetime.timedelta(days=5),
            from_agent=org1,
            resource_type=rti1,
            resource=res1,
            process=proc2,
            context_agent=org1,
            quantity=Decimal(20),
            unit_of_quantity=unit_each,
            commitment=None,
            )
        proc2_e1.save()
        proc3_e1 = EconomicEvent(
            event_type=et_consume,
            event_date=datetime.date.today() + datetime.timedelta(days=10),
            from_agent=org1,
            resource_type=rti3,
            resource=res3,
            process=proc3,
            context_agent=org2,
            quantity=Decimal(1),
            unit_of_quantity=unit_each,
            commitment=None,
            )
        proc3_e1.save()

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
        #import pdb; pdb.set_trace()
        resourceTaxonomyItemsByProcessCategory = result.data['viewer']['resourceTaxonomyItemsByProcessCategory']
        resourceTaxonomyItemsByAction = result.data['viewer']['resourceTaxonomyItemsByAction']
        self.assertEqual(len(resourceTaxonomyItemsByProcessCategory), 1)
        rti1 = resourceTaxonomyItemsByProcessCategory[0]
        self.assertEqual(rti1['name'], 'component1')
        consumed_resources = rti1['taxonomyItemResources']
        self.assertEqual(len(consumed_resources), 2)
        conres1 = consumed_resources[0]
        self.assertEqual(conres1['trackingIdentifier'], 'a-component')
        prod_resources = resourceTaxonomyItemsByAction[1]['taxonomyItemResources']
        prodres1 = prod_resources[0]
        self.assertEqual(prodres1['trackingIdentifier'], 'a-product')

    def test_agent_other_queries(self):
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
                    agent(id: 2) {
                      name
                      ownedEconomicResources(category: INVENTORY) {
                        id
                        resourceTaxonomyItem {
                          name
                          category
                          processCategory
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
                      agentProcesses (isFinished: false) {
                        name
                        isFinished
                      }
                    }
                  }
                }
                '''
        result = schema.execute(query)
        agent = result.data['viewer']['agent']
        ownedEconomicResources = result.data['viewer']['agent']['ownedEconomicResources']
        processes = result.data['viewer']['agent']['agentProcesses']
        self.assertEqual(agent['name'], 'org1')
        self.assertEqual(ownedEconomicResources[0]['resourceTaxonomyItem']['name'], 'product1')
        self.assertEqual(ownedEconomicResources[0]['resourceTaxonomyItem']['processCategory'], 'produced')
        self.assertEqual(len(ownedEconomicResources), 2)
        self.assertEqual(ownedEconomicResources[0]['currentQuantity']['unit']['name'], 'Each')
        self.assertEqual(len(processes), 1)
        self.assertEqual(processes[0]['name'], 'proc1')

    def test_processes_commitments_events(self):
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
                query {
                  viewer(token: "''' + token + '''") {
                    process(id: 1) {
                        name
                        unplannedEconomicEvents(action: PRODUCE) {
                            ...coreEventFields
                        }
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
                        workingAgents {
                            name
                            image
                            __typename
                        }
                    }
                  }
                }
                '''
        result = schema.execute(query)
        process = result.data['viewer']['process']
        self.assertEqual(process['name'], 'proc1')
        unplannedEconomicEvents = process['unplannedEconomicEvents']
        processEconomicEvents = process['processEconomicEvents']
        processCommitments = process['processCommitments']
        inputs = process['inputs']
        workInputs = process['workInputs']
        nonWorkInputs = process['nonWorkInputs']
        outputs = process['outputs']
        committedInputs = process['committedInputs']
        committedWorkInputs = process['committedWorkInputs']
        committedNonWorkInputs = process['committedNonWorkInputs']
        committedOutputs = process['committedOutputs']
        nextProcesses = process['nextProcesses']
        previousProcesses = process['previousProcesses']
        workingAgents = process['workingAgents']
        self.assertEqual(len(unplannedEconomicEvents), 1)
        self.assertEqual(len(processEconomicEvents), 6)
        self.assertEqual(len(processCommitments), 4)
        self.assertEqual(len(inputs), 4)
        self.assertEqual(len(workInputs), 3)
        self.assertEqual(len(nonWorkInputs), 1)
        self.assertEqual(len(outputs), 2)
        self.assertEqual(len(committedInputs), 3)
        self.assertEqual(len(committedWorkInputs), 2)
        self.assertEqual(len(committedNonWorkInputs), 1)
        self.assertEqual(len(committedOutputs), 1)
        self.assertEqual(len(nextProcesses), 1)
        self.assertEqual(len(previousProcesses), 1)
        self.assertEqual(len(workingAgents), 2)
        self.assertEqual(workingAgents[0]['__typename'], "Person")
        self.assertEqual(inputs[0]['action'], "work")
        self.assertEqual(inputs[1]['affectedQuantity']['numericValue'], 1.5)
        self.assertEqual(inputs[2]['affectedResource']['resourceTaxonomyItem']['name'], "component1")
        self.assertEqual(inputs[3]['provider']['name'], "testUser11222")
        self.assertEqual(outputs[0]['action'], "produce")
        self.assertEqual(committedInputs[0]['action'], "work")
        self.assertEqual(committedInputs[1]['committedQuantity']['numericValue'], 2.5)
        self.assertEqual(committedInputs[2]['committedTaxonomyItem']['name'], "component1")
        self.assertEqual(committedInputs[1]['provider']['name'], "not user")
        self.assertEqual(committedOutputs[0]['action'], "produce")
        self.assertEqual(previousProcesses[0]['name'], 'proc2')
        self.assertEqual(nextProcesses[0]['name'], 'proc3')

    def test_create_update_delete_process(self):
        result = schema.execute('''
                mutation { 
                  createProcess(name: "Make something cool", plannedStart: "2017-07-07", 
                    plannedDuration: 7, scopeId: 2, createdById: 1) {
                    process {
                        name
                        scope {
                            name
                        }
                        isFinished
                        plannedStart
                        plannedDuration
                    }
                  }
                }
                ''')

        self.assertEqual(result.data['createProcess']['process']['name'], "Make something cool")
        self.assertEqual(result.data['createProcess']['process']['scope']['name'], "org1")
        self.assertEqual(result.data['createProcess']['process']['isFinished'], False)
        self.assertEqual(result.data['createProcess']['process']['plannedStart'], "2017-07-07")
        self.assertEqual(result.data['createProcess']['process']['plannedDuration'], "7 days, 0:00:00")

        result2 = schema.execute('''
                    mutation {
                        updateProcess(id: 4, plannedDuration: 10, changedById: 1, isFinished: true) {
                            process {
                                name
                                scope {
                                    name
                                }
                                isFinished
                                plannedStart
                                plannedDuration
                            }
                        }
                    }
                    ''')

        self.assertEqual(result2.data['updateProcess']['process']['name'], "Make something cool")
        self.assertEqual(result2.data['updateProcess']['process']['scope']['name'], "org1")
        self.assertEqual(result2.data['updateProcess']['process']['isFinished'], True)
        self.assertEqual(result2.data['updateProcess']['process']['plannedStart'], "2017-07-07")
        self.assertEqual(result2.data['updateProcess']['process']['plannedDuration'], "10 days, 0:00:00")

        result3 = schema.execute('''
                    mutation {
                        deleteProcess(id: 4) {
                            process {
                                name
                            }
                        }
                    }
                    ''')

        proc = None
        try:
            proc = Process.objects.get(pk=4)
        except:
            pass
        self.assertEqual(proc, None)


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
      processCategory
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
      scope {
        name
      }
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
      scope {
        name
      }
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
      unplannedEconomicEvents(action: WORK) {
        ...coreEventFields
      }
      processEconomicEvents {
        ...coreEventFields
      }
      processEconomicEvents(action: PRODUCE) {
        ...coreEventFields
      }
      processCommitments {
        ...coreCommitmentFields
      }
      processCommitments(action: WORK) {
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
      affectedTaxonomyItem {
        name
        category
      }
      affectedResource {
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

######################### SAMPLE MUTATIONS ###########################

mutation {
  createProcess(name: "Make something cool 2", plannedStart: "2017-07-07", 
    plannedDuration: 7, scopeId: 26, createdById: 6) {
    process {
      name
    }
  }
}

mutation {
  updateProcess(id: 59
    plannedDuration: 10, changedById: 6, isFinished: true) {
    process {
      name
      isFinished
      plannedDuration
    }
  }
}

mutation {
  deleteProcess(id: 57) {
    process {
      name
    }
  }
}

'''
