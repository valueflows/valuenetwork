#
# Graphene schema for exposing EconomicAgent and related models
#

#from django.core.exceptions import PermissionDenied

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicEvent as EconomicEventProxy
from valuenetwork.api.models import formatAgent, Person, Organization

import Process.Process

class Action(graphene.Enum):
    NONE = None
    WORK = "work"
    CONSUME = "consume"
    USE = "use"
    CITE = "cite"
    PRODUCE = "produce"
    CHANGE = "change"


class EconomicEvent(DjangoObjectType):
    action = graphene.String(source='action')
    process = graphene.Field(lambda: Process)
    provider = graphene.Field(lambda: Agent)
    receiver = graphene.Field(lambda: Agent)
    scope = graphene.Field(lambda: Agent)
    affected_resource = graphene.Field(lambda: EconomicResource)
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


