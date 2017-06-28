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


class AgentRelationshipCategory(graphene.Enum):
    NONE = None
    MEMBER = "member"
    PART = "part"
    PEER = "peer"
    TRADINGPARTNER = "trading partner" #what is the best way to do the 2 word items?
    LEGALPARTNER = "legal partner"

class AgentRelationshipRole(DjangoObjectType):
    category = graphene.Field(lambda: AgentRelationshipCategory)  #graphene.String(source='category')

    class Meta:
        model = AgentAssociationType
        only_fields = ('id', 'label', 'inverse_label')


