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
#from EconomicResource import EconomicResourceCategory
import valuenetwork.api.types as types
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

    organizations = graphene.List(lambda: Organization)

    owned_economic_resources = graphene.List(lambda: types.EconomicResource,
                                             category=types.EconomicResourceCategory())

    agent_processes = graphene.List(lambda: types.Process,
                                    is_finished=graphene.Boolean())

    economic_events = graphene.List(lambda: types.EconomicEvent,
                                    latest_number_of_days=graphene.Int())

    # Resolvers

    def resolve_organizations(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            return formatAgentList(agent.is_member_of())
        return None

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

    #returns events where an agent is a provider, receiver, or scope agent
    def resolve_economic_events(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            days = args.get('latest_number_of_days', 0)
            if days > 0:
                return agent.involved_in_events().filter(event_date__gte=(datetime.date.today() - datetime.timedelta(days=days)))
            else:
                return agent.involved_in_events()
        return None


# ValueFlows type for a Person (singular) Agent.
# In OCP there are no different properties, but some different behavior/filtering.

class Person(DjangoObjectType):
    class Meta:
        interfaces = (Agent, )
        model = PersonModel #EconomicAgent
        only_fields = ('id', 'name', 'image')


# Organization type- an Agent which is not a Person

class Organization(DjangoObjectType):

    members = graphene.List(lambda: Agent)

    def resolve_members(self, args, context, info):
        org = _load_identified_agent(self)
        if org:
            return formatAgentList(org.members())
        return None


    # Django model binding

    class Meta:
        interfaces = (Agent, )
        model = OrganizationModel #EconomicAgent
        only_fields = ('id', 'name', 'image', 'note')



