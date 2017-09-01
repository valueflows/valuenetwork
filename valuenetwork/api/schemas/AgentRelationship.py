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

    agent_relationship = graphene.Field(AgentRelationship,
                                        id=graphene.Int())

    all_agent_relationships = graphene.List(AgentRelationship)

    # load the relationships of one agent, both directions (subject, object)


    # load agent relationship lists
    
    def resolve_agent_relationship(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            ar = AgentAssociation.objects.get(pk=id)
            if ar:
                return ar
        return None

    def resolve_all_agent_relationships(self, args, context, info):
        return AgentAssociation.objects.all()
