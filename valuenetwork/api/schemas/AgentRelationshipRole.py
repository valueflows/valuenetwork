#
# Agent relationship role schema
#
# @package: OCP
# @author:  Lynn Foster
# @since:   2017-06-10
#

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import AgentAssociationType

# bind Django models to Graphene types.
# This defines which fields are output for matches against each Field/List in Query.

class AgentRelationshipRole(DjangoObjectType):
    label = graphene.String(source='label')
    inverse_label = graphene.String(source='inverse_label')
    class Meta:
        model = AgentAssociationType
        only_fields = ('id')

# define public query API

class Query(graphene.AbstractType):

    all_agent_relationship_roles = graphene.List(AgentRelationshipRole)

    # load agent relationship role list, use to relate relationship label and inverse label

    def resolve_all_agent_relationship_roles(self, args, context, info):
        return AgentAssociationType.objects.all()
