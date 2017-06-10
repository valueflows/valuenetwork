#
# Organisation member typedef.
#
# The same as AgentType but with extra fields relevant to organisational agents.
# This class is mainly to avoid a circular reference between Agent and Organisation.
#
# @package:
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-10
#

import graphene
from . import AgentBase
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicAgent

class OrganizationMemberType(DjangoObjectType):

    id = graphene.String()

    class Meta:
        interfaces = (AgentBase.AgentBaseType, )
        model = EconomicAgent
        only_fields = ('id', 'name')
