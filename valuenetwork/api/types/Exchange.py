#
# Exchange:
#

import graphene
from graphene_django.types import DjangoObjectType
import valuenetwork.api.types as types
from valuenetwork.api.types.QuantityValue import Unit, QuantityValue
from valuenetwork.valueaccounting.models import Exchange, ExchangeType, Transfer as TransferProxy
from valuenetwork.api.models import formatAgent, QuantityValue as QuantityValueProxy


class ExchangeAgreement(DjangoObjectType):
    planned_start = graphene.String(source='planned_start')
    scope = graphene.Field(lambda: types.Agent)
    note = graphene.String(source='note')

    class Meta:
        model = Exchange
        only_fields = ('id', 'name')

    transfers = graphene.List(lambda: types.Transfer)

    involved_agents = graphene.List(lambda: types.Agent)

    def resolve_scope(self, args, *rargs):
        return formatAgent(self.scope)

    def resolve_transfers(self, args, context, info):
        return self.transfers.all()

    def resolve_involved_agents(self, args, context, info):
        agents = self.related_agents()
        formatted_agents = []
        for agent in agents:
            formatted_agents.append(formatAgent(agent))
        return formatted_agents


class Transfer(DjangoObjectType):
    exchange_agreement = graphene.Field(lambda: types.ExchangeAgreement)
    planned_start = graphene.String(source='planned_start')
    scope = graphene.Field(lambda: types.Agent)
    note = graphene.String(source='note')

    class Meta:
        model = TransferProxy
        only_fields = ('id', 'name')

    #this group of fields come from the give and/or take events that make up the transfer
    provider = graphene.Field(lambda: types.Agent)
    receiver = graphene.Field(lambda: types.Agent)
    resource_taxonomy_item = graphene.Field(lambda: types.ResourceTaxonomyItem)
    give_resource = graphene.Field(lambda: types.EconomicResource)
    take_resource = graphene.Field(lambda: types.EconomicResource)
    transfer_quantity = graphene.Field(QuantityValue)
    ###

    transfer_economic_events = graphene.List(lambda: types.EconomicEvent)

    give_economic_event = graphene.Field(lambda: types.EconomicEvent)

    take_economic_event = graphene.Field(lambda: types.EconomicEvent)

    transfer_commitments = graphene.List(lambda: types.Commitment)

    give_commitment = graphene.Field(lambda: types.Commitment)

    take_commitment = graphene.Field(lambda: types.Commitment)

    involved_agents = graphene.List(lambda: types.Agent)

    def resolve_exchange_agreement(self, args, *rargs):
        return self.exchange_agreement

    def resolve_scope(self, args, *rargs):
        return formatAgent(self.scope)

    def resolve_provider(self, args, *rargs):
        return formatAgent(self.provider)

    def resolve_receiver(self, args, *rargs):
        return formatAgent(self.receiver)

    def resolve_resource_taxonomy_item(self, args, *rargs):
        return self.resource_taxonomy_item

    def resolve_give_resource(self, args, *rargs):
        return self.give_resource

    def resolve_take_resource(self, args, *rargs):
        return self.take_resource

    def resolve_transfer_quantity(self, args, *rargs):
        return QuantityValueProxy(numeric_value=self.actual_quantity(), unit=self.unit)

    def resolve_transfer_economic_events(self, args, context, info):
        return self.events.all()

    def resolve_give_economic_event(self, args, *rargs):
        return self.give_event()

    def resolve_take_economic_event(self, args, *rargs):
        return self.receive_event()

    def resolve_give_commitment(self, args, *rargs):
        return self.give_commitment()

    def resolve_take_commitment(self, args, *rargs):
        return self.receive_commitment()

    def resolve_transfer_commitments(self, args, context, info):
        return self.commitments.all()

    def resolve_involved_agents(self, args, context, info):
        agents = self.related_agents()
        formatted_agents = []
        for agent in agents:
            formatted_agents.append(formatAgent(agent))
        return formatted_agents
