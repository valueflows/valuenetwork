#
# Graphene schema for exposing EconomicAgent model
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

from django.core.exceptions import PermissionDenied

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicAgent, AgentUser
from valuenetwork.api.schemas.helpers import *

# bind Django models to Graphene types

class EconomicAgentType(DjangoObjectType):
    class Meta:
        model = EconomicAgent
        only_fields =  ('id', 'name', 'nick', 'url', 'is_context')

# define public query API

class Query(graphene.AbstractType):

    # define input query params

    agent = graphene.Field(EconomicAgentType,
                        me=graphene.Boolean(),
                        nick=graphene.String(),
                        name=graphene.String())

    all_agents = graphene.List(EconomicAgentType)

    # load single agents

    def resolve_agent(self, args, context, info):
        me = args.get('me')
        nick = args.get('nick')
        name = args.get('name')

        # load own agent

        if (me is not None):
            if not context.user.is_authenticated():
                raise PermissionDenied
            else:
                agentUser = AgentUser.objects.filter(user=context.user.id).first()
                if (agentUser is None):
                    raise PermissionDenied
                return agentUser.agent

        # read by nickname

        if (nick is not None):
            return ensureSingleModel(EconomicAgent.objects.filter(nick=nick))

        # read by name

        if (name is not None):
            return ensureSingleModel(EconomicAgent.objects.filter(name=name))

    # load agents list

    def resolve_all_agents(self, args, context, info):
        return EconomicAgent.objects.all()
