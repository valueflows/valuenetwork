#
# Plan: A set of one or more connected processes. (Note there is currently no corresponding ValueFlows concept, although something like it will probably need to be added.  But for now, this is not VF vocabulary compliant.)
#

import graphene
from graphene_django.types import DjangoObjectType
import valuenetwork.api.types as types
from valuenetwork.api.types.EconomicEvent import Action
from valuenetwork.valueaccounting.models import Order
from valuenetwork.api.models import formatAgent, formatAgentList


class Plan(DjangoObjectType):
    planned_on = graphene.String(source='planned')
    due = graphene.String(source='due')
    note = graphene.String(source='note')
    name = graphene.String(source='plan_name')

    class Meta:
        model = Order
        only_fields = ('id')


    scope = graphene.List(lambda: types.Agent)

    plan_processes = graphene.List(lambda: types.Process)

    working_agents = graphene.List(lambda: types.Agent)

    planned_non_work_inputs = graphene.List(lambda: types.Commitment)

    planned_outputs = graphene.List(lambda: types.Commitment)

    non_work_inputs = graphene.List(lambda: types.EconomicEvent)

    outputs = graphene.List(lambda: types.EconomicEvent)

    kanban_state = graphene.String()

    def resolve_scope(self, args, *rargs):
        return formatAgentList(self.plan_context_agents())

    def resolve_plan_processes(self, args, context, info):
        return self.all_processes()

    def resolve_working_agents(self, args, context, info):
        return formatAgentList(self.all_working_agents())

    def resolve_planned_non_work_inputs(self, args, context, info):
        return self.non_work_incoming_commitments()

    def resolve_planned_outputs(self, args, context, info):
        return self.all_outgoing_commitments()

    def resolve_non_work_inputs(self, args, context, info):
        return self.non_work_incoming_events()

    def resolve_outputs(self, args, context, info):
        return self.all_outgoing_events()

    # returns "planned", "doing", "done"
    def resolve_kanban_state(self, args, *rargs):
        return self.kanban_state()
