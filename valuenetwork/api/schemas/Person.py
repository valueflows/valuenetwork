#
# Graphene schema for exposing individual user query endpoints ("Person" in VF terms)
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-06-20
#

import graphene

from valuenetwork.valueaccounting.models import EconomicAgent

from AgentBaseQueries import AgentBase
from valuenetwork.api.types.Agent import Person
from valuenetwork.api.models import formatAgent, formatAgentList

class Query(AgentBase, graphene.AbstractType):

    # define input query params

    person = graphene.List(Person)

    all_people = graphene.List(Person)

    # load any person

    def resolve_organization(self, args, context, info):
        id = args.get('id')
        if id is not None:
            return formatAgent(EconomicAgent.objects.get(pk=id, is_context=False))    # :TODO: @fosterlynn what's correct here?
        return None

    # load all people

    def resolve_all_people(self, args, context, info):
        return formatAgentList(EconomicAgent.objects.all(is_context=False))  # :TODO: @fosterlynn what's correct here?
