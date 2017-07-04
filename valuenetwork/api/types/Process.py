#
# Process: An activity that changes inputs into outputs.  It could transform or transport EconomicResource(s), as well as simply issuing a resource so that it is available.
#

import graphene
from graphene_django.types import DjangoObjectType
import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import Process as ProcessProxy


class Process(DjangoObjectType):
    planned_start = graphene.String(source='planned_start')
    planned_duration = graphene.String(source='planned_duration')
    is_finished = graphene.Boolean(source='is_finished')
    note = graphene.String(source='note')

    class Meta:
        model = ProcessProxy
        only_fields = ('id', 'name')


    inputs = graphene.List(lambda: types.EconomicEvent)

    outputs = graphene.List(lambda: types.EconomicEvent)

    committed_inputs = graphene.List(lambda: types.Commitment)

    committed_outputs = graphene.List(lambda: types.Commitment)

    next_processes = graphene.List(lambda: types.Process)

    previous_processes = graphene.List(lambda: types.Process)
    
    def resolve_inputs(self, args, context, info):
        return self.incoming_events()

    def resolve_outputs(self, args, context, info):
        return self.outputs()

    def resolve_committed_inputs(self, args, context, info):
        return self.incoming_commitments()

    def resolve_committed_outputs(self, args, context, info):
        return self.outgoing_commitments()

    def resolve_next_processes(self, args, context, info):
        return self.next_processes()

    def resolve_previous_processes(self, args, context, info):
        return self.previous_processes()
