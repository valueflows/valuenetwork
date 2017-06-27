#
# Process: 

import graphene
from graphene_django.types import DjangoObjectType
import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import Process as ProcessProxy


class Process(DjangoObjectType):
    planned_start = graphene.String(source='planned_start')
    planned_duration = graphene.String(source='planned_duration')
    is_finished = graphene.String(source='is_finished')
    note = graphene.String(source='note')

    class Meta:
        model = ProcessProxy
        only_fields = ('id', 'name')


    inputs = graphene.List(lambda: types.EconomicEvent)
    
    outputs = graphene.List(lambda: types.EconomicEvent)


    def resolve_inputs(self, args, context, info):
        return self.incoming_events()

    def resolve_outputs(self, args, context, info):
        return self.outputs()

