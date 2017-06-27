#
# Graphene schema for exposing organisation Agent relationships
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-05
#

import graphene

from valuenetwork.valueaccounting.models import EconomicAgent

from AgentBaseQueries import AgentBase
from valuenetwork.api.types.Agent import Organization
from valuenetwork.api.models import formatAgent, formatAgentList

class Query(AgentBase, graphene.AbstractType):

    # define input query params

    my_organizations = graphene.List(Organization)

    organization = graphene.Field(Organization,
                                  id=graphene.Int())

    all_organizations = graphene.List(Organization)

    # load context agents that 'me' is related to with 'member' or 'manager' behavior
    # (this gives the projects, collectives, groups that the user agent is any
    # kind of member of)

    def resolve_my_organizations(self, args, context, info):
        my_agent = self._load_own_agent() # provided by AgentBase
        return formatAgentList(my_agent.is_member_of())

    # load any organisation

    def resolve_organization(self, args, context, info):
        id = args.get('id')
        if id is not None:
            #return formatAgent(EconomicAgent.objects.get(pk=id, agent_type__party_type!="individual"))  didn't compile
            org = EconomicAgent.objects.get(pk=id)
            if org:
                if org.agent_type.party_type == "individual":
                    return None
                else:
                    return formatAgent(org)
            else:
                return None
        return None

    # load all organizations

    def resolve_all_organizations(self, args, context, info):
        return formatAgentList(EconomicAgent.objects.filter(agent_type__party_type!="individual"))
