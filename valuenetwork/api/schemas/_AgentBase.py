#
# Base class for all EconomicAgent types
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-10
#

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicAgent

class AgentBase(DjangoObjectType):
    type = graphene.String(source='type')
    image = graphene.String(source='image')
    note = graphene.String(source='note')
    class Meta:
        model = EconomicAgent
        only_fields = ('id', 'name')
