#
# EconomicAgent type def and subclasses
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-10
#

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicAgent
from EconomicResource import EconomicResourceCategory, EconomicResource
from Process import Process
from EconomicEvent import EconomicEvent


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

    owned_economic_resources = graphene.List(lambda: EconomicResource, 
                                             category=EconomicResourceCategory())

    agent_processes = graphene.List(lambda: Process,
                                    is_finished=graphene.Boolean())

    economic_events = graphene.List(lambda: EconomicEvent)

    # Resolvers

    def resolve_organizations(self, args, context, info):
        agent = _load_identified_agent(self)
        if agent:
            return agent.is_member_of()
        return None

    def resolve_owned_economic_resources(self, args, context, info):
        type = args.get('category', EconomicResourceCategory.NONE)
        org = _load_identified_agent(self)
        if org:
            if type == EconomicResourceCategory.CURRENCY:
                return org.owned_currency_resources()
            elif type == EconomicResourceCategory.INVENTORY:
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
            return agent.involved_in_events()
        return None


# ValueFlows type for a Person (singular) Agent.
# In OCP these don't have anything a regular Agent doesn't have, but the distinction is important for ValueFlows.

class Person(DjangoObjectType):
    class Meta:
        interfaces = (Agent, )
        model = EconomicAgent
        only_fields = ('id', 'name')


# Organization type- an Agent which can have other Agents as members

class Organization(DjangoObjectType):

    members = graphene.List(lambda: Agent)

    def resolve_members(self, args, context, info):
        org = _load_identified_agent(self)
        if org:
            return org.members()
        return None


    # Django model binding

    class Meta:
        interfaces = (Agent, )
        model = EconomicAgent
        only_fields = ('id', 'name')
