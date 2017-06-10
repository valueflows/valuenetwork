#
# EconomicAgent type def
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-10
#

import graphene
from . import AgentBase, Organization
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicAgent

class AgentType(DjangoObjectType):

    id = graphene.String()  # This will get filled by schemas.Agent.Query for any agent bound to the graphene.Field. Magic!

    organizations = graphene.List(Organization.OrganizationType)

    def resolve_organizations(self, args, context, info):
        agent = EconomicAgent.objects.get(pk=self.id)   # you can reference input data on `self`.
        return agent.is_member_of()

    class Meta:
        interfaces = (AgentBase.AgentBaseType, )
        model = EconomicAgent
        only_fields = ('id', 'name')
