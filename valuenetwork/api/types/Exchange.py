#
# Process: An activity that changes inputs into outputs.  It could transform or transport EconomicResource(s), as well as simply issuing a resource so that it is available.
#

import graphene
from graphene_django.types import DjangoObjectType
import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import Exchange, ExchangeType
from valuenetwork.api.models import formatAgent


class ExchangeAgreement(DjangoObjectType):
    planned_start = graphene.String(source='planned_start')
    note = graphene.String(source='note')

    class Meta:
        model = Exchange
        only_fields = ('id', 'name')


    exchange_economic_events = graphene.List(lambda: types.EconomicEvent)

    exchange_commitments = graphene.List(lambda: types.Commitment)

    involved_agents = graphene.List(lambda: types.Agent)

    def resolve_exchange_economic_events(self, args, context, info):
        return self.events.all()

    def resolve_exchange_commitments(self, args, context, info):
        return self.commitments.all()

    def resolve_involved_agents(self, args, context, info):
        agents = self.all_working_agents()
        formatted_agents = []
        for agent in agents:
            formatted_agents.append(formatAgent(agent))
        return formatted_agents
