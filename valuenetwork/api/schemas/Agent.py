#
# Graphene schema for exposing EconomicAgent and related models
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

from django.core.exceptions import PermissionDenied
import graphene
from valuenetwork.valueaccounting.models import EconomicAgent, AgentUser
from valuenetwork.api.models import formatAgent, formatAgentList
from valuenetwork.api.types.Agent import Agent

class Query(graphene.AbstractType):

    # define input query params

    my_agent = graphene.Field(Agent)

    agent = graphene.Field(Agent,
                           id=graphene.Int())

    all_agents = graphene.List(Agent)

    # load single agents

    def resolve_my_agent(self, args, *rargs):
        agentUser = AgentUser.objects.filter(user=self.user).first()
        agent = agentUser.agent
        if agent:
            return formatAgent(agent)
        raise PermissionDenied("Cannot find requested agent")

    def resolve_agent(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            agent = EconomicAgent.objects.get(pk=id)
            if agent:
                return formatAgent(agent)
        raise PermissionDenied("Cannot find requested agent")

    # load all agent lists

    def resolve_all_agents(self, args, context, info):
        return formatAgentList(EconomicAgent.objects.all())
