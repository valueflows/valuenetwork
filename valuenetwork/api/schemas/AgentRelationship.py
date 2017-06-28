#
# Agent relationship entity schema def
#
# @package: OCP
#

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.api.types.AgentRelationship import AgentRelationship
from valuenetwork.valueaccounting.models import EconomicAgent, AgentAssociation

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
