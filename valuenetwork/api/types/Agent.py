#
# EconomicAgent:A person or group or organization with economic agency.
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-10
#

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicAgent
import valuenetwork.api.types as types
from valuenetwork.api.types.AgentRelationship import AgentRelationship
from valuenetwork.api.types.AgentRelationshipRole import AgentRelationshipCategory, AgentRelationshipRole
from valuenetwork.api.models import Organization as OrganizationModel, Person as PersonModel, formatAgentList
import datetime


def _load_identified_agent(self):
    return EconomicAgent.objects.get(pk=self.id)


# Economic agent base type

class Agent(graphene.Interface):

    # fields common to all agent types

    id = graphene.String()
    name = graphene.String()
    type = graphene.String(source='type')
    image = graphene.String(source='image')
    note = graphene.String(source='note')

    owned_economic_resources = graphene.List(lambda: types.EconomicResource,
                                             category=types.EconomicResourceCategory())

    agent_processes = graphene.List(lambda: types.Process,
                                    is_finished=graphene.Boolean())

    agent_economic_events = graphene.List(lambda: types.EconomicEvent,
                                          latest_number_of_days=graphene.Int())

    agent_commitments = graphene.List(lambda: types.Commitment,
                                      latest_number_of_days=graphene.Int())

    agent_relationships = graphene.List(AgentRelationship,
                                        role_id=graphene.Int(),
                                        category=AgentRelationshipCategory())

    agent_roles = graphene.List(AgentRelationshipRole)

    # Resolvers

    def resolve_owned_economic_resources(self, args, context, info):
        type = args.get('category', types.EconomicResourceCategory.NONE)
        org = _load_identified_agent(self)
        if org:
            if type == types.EconomicResourceCategory.CURRENCY:
                return org.owned_currency_resources()
            elif type == types.EconomicResourceCategory.INVENTORY:
                return org.owned_inventory_resources()
            return org.owned_resources()
        return None

    # if an organization, this returns processes done in that context
    # if a person, this returns proceses the person has worked on
    def resolve_agent_processes(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            agent_processes = agent.all_processes()
            finished = args.get('is_finished', None)
            if finished != None:
                if not finished:
                    return agent_processes.filter(finished=False)
                else:
                    return agent_processes.filter(finished=True)
            else:
                return agent_processes
        return None

    # returns events where an agent is a provider, receiver, or scope agent
    def resolve_agent_economic_events(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            days = args.get('latest_number_of_days', 0)
            if days > 0:
                return agent.involved_in_events().filter(event_date__gte=(datetime.date.today() - datetime.timedelta(days=days)))
            else:
                return agent.involved_in_events()
        return None

    # returns commitments where an agent is a provider, receiver, or scope agent
    def resolve_agent_commitments(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            days = args.get('latest_number_of_days', 0)
            if days > 0:
                return agent.involved_in_commitments().filter(commitment_date__gte=(datetime.date.today() - datetime.timedelta(days=days)))
            else:
                return agent.involved_in_commitments()
        return None

    # returns relationships where an agent is a subject or object, optionally filtered by role category
    def resolve_agent_relationships(self, args, context, info):
        agent = _load_identified_agent(self)
        cat = args.get('category')
        role_id = args.get('role_id')
        if agent:
            assocs = agent.all_active_associations()
            filtered_assocs = []
            if role_id: #try the most specific first
                for assoc in assocs:
                    if assoc.association_type.id == role_id:
                        filtered_assocs.append(assoc)
                return filtered_assocs
            if cat:
                for assoc in assocs:
                    if assoc.association_type.category == cat:
                        filtered_assocs.append(assoc)
                return filtered_assocs
            else:
                return agent.all_active_associations()
        return None

    # returns relationships where an agent is a subject or object, optionally filtered by role category
    def resolve_agent_roles(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            return agent.active_association_types()
        return None


# ValueFlows type for a Person (singular) Agent.
# In OCP there are no different properties, but some different behavior/filtering.

class Person(DjangoObjectType):
    class Meta:
        interfaces = (Agent, )
        model = PersonModel #EconomicAgent
        only_fields = ('id', 'name', 'image')


# Organization - an Agent which is not a Person, and can be further classified from there

class Organization(DjangoObjectType):

    class Meta:
        interfaces = (Agent, )
        model = OrganizationModel #EconomicAgent
        only_fields = ('id', 'name', 'image', 'note')



