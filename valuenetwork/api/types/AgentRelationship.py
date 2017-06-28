#
# Agent Relationship: An ongoing voluntary association between 2 Agents of any kind.
#

import graphene
from graphene_django.types import DjangoObjectType
import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import AgentAssociation


class AgentRelationship(DjangoObjectType):
    subject = graphene.Field(lambda: types.Agent)
    object = graphene.Field(lambda: types.Agent)
    relationship = graphene.Field(lambda: types.AgentRelationshipRole)

    class Meta:
        model = AgentAssociation
        only_fields = ('id')