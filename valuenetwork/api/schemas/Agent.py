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
from valuenetwork.api.models import Organization, Person

from AgentBaseQueries import AgentBase
from valuenetwork.api.types.Agent import Agent

class Query(AgentBase, graphene.AbstractType):

    # define input query params

    my_agent = graphene.Field(Agent)

    agent = graphene.Field(Agent,
                           id=graphene.Int())

    all_agents = graphene.List(Agent)

    # load single agents

    def resolve_my_agent(self, args, *rargs):
        agent = self._load_own_agent()
        if agent:
            return agent
        raise PermissionDenied("Cannot find requested agent")

    def resolve_agent(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            agent = EconomicAgent.objects.get(pk=id)
            if agent:
                return agent
        raise PermissionDenied("Cannot find requested agent")

    # load all agent lists

    def resolve_all_agents(self, args, context, info):
        #return EconomicAgent.objects.all()
        all_agents = EconomicAgent.objects.all()
        mixed_list = []
        for agent in all_agents:
            if agent.agent_type.party_type == "individual":
                person = Person(
                    id=agent.id,
                    name = agent.name,
                    note = agent.description,
                    image = agent.image)
                mixed_list.append(person)
            else:
                org = Organization(
                    id=agent.id,
                    name = agent.name,
                    note = agent.description,
                    image = agent.image,
                    is_context = agent.is_context,
                    type = agent.agent_type)
                mixed_list.append(org)
        return mixed_list
