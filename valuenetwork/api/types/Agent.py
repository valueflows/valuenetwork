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
from . import OrganizationResource, OrganizationProcess
from EconomicResourceBase import EconomicResourceCategory


# Helpers (can't call between methods of the base class since DjangoObjectType
# overrides `self` to be the bound Django model instance)

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

    owned_economic_resources = graphene.List(OrganizationResource.OrganizationResource,
                                            category=EconomicResourceCategory())

    unfinished_processes = graphene.List(OrganizationProcess.OrganizationProcess)

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

    def resolve_unfinished_processes(self, args, context, info):
        org = _load_identified_agent(self)
        if org:
            return org.active_context_processes()
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
