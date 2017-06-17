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
from . import AgentBase, OrganizationResource, OrganizationProcess


# Economic agent base type

class Agent(graphene.Interface):

    # fields common to all agent types

    id = graphene.String()
    name = graphene.String()
    type = graphene.String(source='type')
    image = graphene.String(source='image')
    note = graphene.String(source='note')

    organizations = graphene.List(lambda: Organization)

    owned_economic_resources = graphene.List(OrganizationResource.OrganizationResource)

    owned_currency_economic_resources = graphene.List(OrganizationResource.OrganizationResource)

    owned_inventory_economic_resources = graphene.List(OrganizationResource.OrganizationResource)

    unfinished_processes = graphene.List(OrganizationProcess.OrganizationProcess)

    # Resolvers

    def resolve_organizations(self, args, context, info):
        agent = EconomicAgent.objects.get(pk=self.id)   # you can reference input data on `self`.
        return agent.is_member_of()

    def resolve_owned_economic_resources(self, args, context, info):
        org = EconomicAgent.objects.get(pk=self.id)
        if org:
            return org.owned_resources()
        return None

    def resolve_owned_currency_economic_resources(self, args, context, info):
        org = EconomicAgent.objects.get(pk=self.id)
        if org:
            return org.owned_currency_resources()
        return None

    def resolve_owned_inventory_economic_resources(self, args, context, info):
        org = EconomicAgent.objects.get(pk=self.id)
        if org:
            return org.owned_inventory_resources()
        return None

    def resolve_unfinished_processes(self, args, context, info):
        org = EconomicAgent.objects.get(pk=self.id)
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
        org = EconomicAgent.objects.get(pk=self.id)
        if org:
            return org.members()
        return None

    # Django model binding

    class Meta:
        interfaces = (Agent, )
        model = EconomicAgent
        only_fields = ('id', 'name')
