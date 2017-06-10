#
# Organisation type def
#
# The same as AgentType but with extra fields relevant to organisational agents
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-10
#

import graphene
from . import AgentBase, OrganizationMember
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicAgent

class OrganizationType(DjangoObjectType):

    id = graphene.String()

    members = graphene.List(OrganizationMember.OrganizationMemberType)

    def resolve_members(self, args, context, info):
        org = EconomicAgent.objects.get(pk=self.id)
        if org:
            return org.members()

    class Meta:
        interfaces = (AgentBase.AgentBaseType, )
        model = EconomicAgent
        only_fields = ('id', 'name')
