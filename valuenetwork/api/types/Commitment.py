#
# Commitment: A planned economic event or transfer that has been promised by an agent to another agent..
#


import graphene
from graphene_django.types import DjangoObjectType

import valuenetwork.api.types as types
from valuenetwork.api.types.EconomicEvent import Action
from valuenetwork.valueaccounting.models import Commitment as CommitmentProxy
from valuenetwork.api.models import formatAgent, Person, Organization


class Commitment(DjangoObjectType):
    action = graphene.String(source='action')
    process = graphene.Field(lambda: types.Process)
    provider = graphene.Field(lambda: types.Agent)
    receiver = graphene.Field(lambda: types.Agent)
    scope = graphene.Field(lambda: types.Agent)
    committed_resource = graphene.Field(lambda: types.EconomicResource)
    #committed_taxonomy_item = graphene.Field(
    numeric_value = graphene.Float(source='numeric_value') #need to implement as quantity-value with unit
    unit = graphene.String(source='unit')
    start = graphene.String(source='start')
    work_category = graphene.String(source='work_category')
    note = graphene.String(source='note')

    class Meta:
        model = EconomicEventProxy
        only_fields = ('id')

    def resolve_process(self, args, *rargs):
        return self.process

    def resolve_provider(self, args, *rargs):
        return formatAgent(self.provider)

    def resolve_receiver(self, args, *rargs):
        return formatAgent(self.receiver)

    def resolve_scope(self, args, *rargs):
        return formatAgent(self.scope)

    def resolve_affected_resource(self, args, *rargs):
        return self.affected_resource


