#
# Graphene schema for exposing organisation Agent relationships
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-05
#

import graphene

from valuenetwork.valueaccounting.models import EconomicAgent
from valuenetwork.api.schemas.Agent import Agent    # :NOTE: an Organisation is just an Agent which is a context

# define public query API

class Query(graphene.AbstractType):

    # define input query params

    my_organizations = graphene.List(Agent)

    organization = graphene.Field(Agent,
                                  id=graphene.Int())

    organization_members = graphene.List(Agent,
                                         org_id=graphene.Int())

    # load context agents that 'me' is related to with 'member' or 'manager' behavior
    # (this gives the projects, collectives, groups that the user agent is any
    # kind of member of)

    def resolve_my_organizations(self, args, context, info):
        my_agent = self._load_own_agent()
        return my_agent.is_member_of()

    # load any organisation

    def resolve_organization(self, args, context, info):
        id = args.get('id')
        if id is not None:
            return EconomicAgent.objects.get(pk=id, is_context=True)
        return None

    # load members (agents) of an organization (context agent)

    def resolve_organization_members(self, args, context, info):
        id = args.get('org_id')
        if id is not None:
            org = EconomicAgent.objects.get(pk=id)
            if org:
                return org.members()
        return None
