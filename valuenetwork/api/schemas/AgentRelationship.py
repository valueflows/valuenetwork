#
# Agent relationship entity schema def
#
# @package: OCP
# @author:  Lynn Foster
# @since:   2017-06-10
#

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicAgent, AgentAssociation

# bind Django models to Graphene types.
# This defines which fields are output for matches against each Field/List in Query.

class AgentRelationship(DjangoObjectType):
    subject = graphene.String(source='subject')
    object = graphene.String(source='object')
    relationship = graphene.String(source='relationship')
    class Meta:
        model = AgentAssociation
        only_fields = ('id')

# define public query API

class Query(graphene.AbstractType):

    agent_relationships = graphene.List(AgentRelationship,
                                        id=graphene.Int())

    all_agent_relationships = graphene.List(AgentRelationship)

    # load the relationships of one agent, both directions (subject, object)

    def resolve_agent_relationships(self, args, context, info):
        id = args.get('id')
        if id is not None:
            agent = EconomicAgent.objects.get(pk=id)
            if agent:
                return agent.all_active_associations()
        return None

    # load agent relationship lists

    def resolve_all_agent_relationships(self, args, context, info):
        return AgentAssociation.objects.all()
