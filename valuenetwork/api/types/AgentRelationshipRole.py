#
# Agent relationship role schema
#

import graphene
from graphene_django.types import DjangoObjectType
from valuenetwork.valueaccounting.models import AgentAssociationType


class AgentRelationshipCategory(graphene.Enum):
    NONE = None
    MEMBER = "member"
    PART = "part"
    PEER = "peer"
    TRADINGPARTNER = "trading partner"
    LEGALPARTNER = "legal partner"

class AgentRelationshipRole(DjangoObjectType):
    category = graphene.Field(lambda: AgentRelationshipCategory)  #graphene.String(source='category')

    class Meta:
        model = AgentAssociationType
        only_fields = ('id', 'label', 'inverse_label')

    def resolve_category(self, args, *rargs):
        return self.category
