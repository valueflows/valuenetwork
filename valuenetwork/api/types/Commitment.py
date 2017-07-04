#
# Commitment: A planned economic event or transfer that has been promised by an agent to another agent.
#


import graphene
from graphene_django.types import DjangoObjectType

import valuenetwork.api.types as types
from valuenetwork.api.types.QuantityValue import Unit, QuantityValue
from valuenetwork.valueaccounting.models import Commitment as CommitmentProxy
from valuenetwork.api.models import formatAgent, Person, Organization, QuantityValue as QuantityValueProxy


class Commitment(DjangoObjectType):
    action = graphene.String(source='action')
    process = graphene.Field(lambda: types.Process)
    provider = graphene.Field(lambda: types.Agent)
    receiver = graphene.Field(lambda: types.Agent)
    scope = graphene.Field(lambda: types.Agent)
    committed_taxonomy_item = graphene.Field(lambda: types.ResourceTaxonomyItem)
    committed_resource = graphene.Field(lambda: types.EconomicResource)
    committed_quantity = graphene.Field(QuantityValue)
    committed_on = graphene.String(source='committed_on')
    commitment_start = graphene.String(source='commitment_start')
    due = graphene.String(source='due')
    is_finished = graphene.Boolean(source='is_finished')
    note = graphene.String(source='note')

    class Meta:
        model = CommitmentProxy
        only_fields = ('id')

    fulfilled_by = graphene.List(lambda: types.EconomicEvent)

    def resolve_process(self, args, *rargs):
        return self.process

    def resolve_provider(self, args, *rargs):
        return formatAgent(self.provider)

    def resolve_receiver(self, args, *rargs):
        return formatAgent(self.receiver)

    def resolve_scope(self, args, *rargs):
        return formatAgent(self.scope)

    def resolve_committed_resource(self, args, *rargs):
        return self.committed_resource

    def resolve_committed_taxonomy_item(self, args, *rargs):
        return self.committed_taxonomy_item

    def resolve_committed_quantity(self, args, *rargs):
        return QuantityValueProxy(numeric_value=self.quantity, unit=self.unit_of_quantity)

    def resolve_fulfilled_by(self, args, context, info):
        return self.fulfilled_by.all()
