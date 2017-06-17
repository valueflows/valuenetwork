#
# Graphene schema for exposing organisation Agent relationships
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-05
#

import graphene

from valuenetwork.valueaccounting.models import EconomicAgent

from valuenetwork.api.types.Agent import AgentType

class Query(graphene.AbstractType):

    # define input query params

    my_organizations = graphene.List(AgentType)

    organization = graphene.Field(AgentType,
                                  id=graphene.Int())

    # load context agents that 'me' is related to with 'member' or 'manager' behavior
    # (this gives the projects, collectives, groups that the user agent is any
    # kind of member of)

    def resolve_my_organizations(self, args, context, info):
        my_agent = self._load_own_agent()   # :NOTE: this method is defined in Agent.py and available via multiple inheritance in ViewerQuery
        return my_agent.is_member_of()

    # load any organisation

    def resolve_organization(self, args, context, info):
        id = args.get('id')
        if id is not None:
            return EconomicAgent.objects.get(pk=id, is_context=True)    # :TODO: @fosterlynn what's correct here?
        return None
