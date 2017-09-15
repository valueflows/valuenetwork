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

    class Meta:
        model = Order
        only_fields = ('id', 'name')


    scope = graphene.List(lambda: types.Agent)

    plan_processes = graphene.List(lambda: types.Process)

    working_agents = graphene.List(lambda: types.Agent)

    planned_input_resources = graphene.List(lambda: types.EconomicResource)

    planned_output_resources = graphene.List(lambda: types.EconomicResource)

    input_resources = graphene.List(lambda: types.EconomicResource)

    output_resources = graphene.List(lambda: types.EconomicResource)

    def resolve_scope(self, args, *rargs):
        return formatAgentList(self.plan_context_agents())

    def resolve_plan_processes(self, args, context, info):
        return self.all_processes()

    def resolve_working_agents(self, args, context, info):
        return formatAgentList(self.all_working_agents())

    def resolve_committed_input_resources(self, args, context, info):
        return self.committed_input_resources()

    def resolve_committed_output_resources(self, args, context, info):
        return self.committed_output_resources()

    def resolve_input_resources(self, args, context, info):
        return self.input_resources()

    def resolve_output_resources(self, args, context, info):
        return self.output_resources()
