#
# Graphene schema for exposing EconomicAgent model
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

from django.core.exceptions import PermissionDenied

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicAgent, AgentUser, AgentAssociation, AgentAssociationType
from valuenetwork.api.schemas.helpers import *

# bind Django models to Graphene types


class Agent(DjangoObjectType):
    type = graphene.String(source='type')
    image = graphene.String(source='image')
    note = graphene.String(source='note')
    class Meta:
        model = EconomicAgent
        only_fields = ('id', 'name')

class AgentRelationship(DjangoObjectType):
    subject = graphene.String(source='subject')
    object = graphene.String(source='object')
    relationship = graphene.String(source='relationship')
    class Meta:
        model = AgentAssociation
        only_fields = ('id')

class AgentRelationshipRole(DjangoObjectType):
    label = graphene.String(source='label')
    inverse_label = graphene.String(source='inverse_label')
    class Meta:
        model = AgentAssociationType
        only_fields = ('id')

# define public query API

class Query(graphene.AbstractType):

    # define input query params

    my_agent = graphene.Field(Agent)

    agent = graphene.Field(Agent,
                           id=graphene.Int())

    all_agents = graphene.List(Agent)

    my_organizations = graphene.List(Agent,
                                     me=graphene.Boolean())

    all_agent_relationship_roles = graphene.List(AgentRelationshipRole)

    all_agent_relationships = graphene.List(AgentRelationship)

    organization_members = graphene.List(Agent,
                                         id=graphene.Int())

    agent_relationships = graphene.List(AgentRelationship,
                                        id=graphene.Int())

    # load single agents

    def _load_own_agent(self):
        agentUser = AgentUser.objects.filter(user=self.user).first()
        return agentUser.agent

    def resolve_my_agent(self, args, *rargs):
        agent = self._load_own_agent()
        if agent:
            return agent
        raise PermissionDenied("Cannot find requested user")

    def resolve_agent(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            agent = EconomicAgent.objects.get(pk=id)
            if agent:
                return agent
        raise PermissionDenied("Cannot find requested agent")        

    # load all agent lists

    def resolve_all_agents(self, args, context, info):
        return EconomicAgent.objects.all()

    # load context agents that 'me' is related to with 'member' or 'manager' behavior
    # (this gives the projects, collectives, groups that the user agent is any
    # kind of member of)

    def resolve_my_organizations(self, args, context, info):
        my_agent = self._load_own_agent()
        return my_agent.is_member_of()
    
    # load members (agents) of an organization (context agent)

    def resolve_organization_members(self, args, context, info):
        id = args.get('id')
        if id is not None:
            org = EconomicAgent.objects.get(pk=id)
            if org:
                return org.members()
        return None

    # load agent relationship role list, use to relate relationship label and inverse label

    def resolve_all_agent_relationship_roles(self, args, context, info):
        return AgentAssociationType.objects.all()

    # load agent relationship lists

    def resolve_all_agent_relationships(self, args, context, info):
        return AgentAssociation.objects.all()

    # load the relationships of one agent, both directions (subject, object)

    def resolve_agent_relationships(self, args, context, info):
        id = args.get('id')
        if id is not None:
            agent = EconomicAgent.objects.get(pk=id)
            if agent:
                return agent.all_active_associations()
        return None
