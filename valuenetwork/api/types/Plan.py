#
# Plan: A set of one or more connected processes. (Note there is currently no corresponding ValueFlows concept, although something like it will probably need to be added.  But for now, this is not VF vocabulary compliant.)
#

import graphene
from graphene_django.types import DjangoObjectType
import valuenetwork.api.types as types
from valuenetwork.api.types.EconomicEvent import Action
from valuenetwork.valueaccounting.models import Order
from valuenetwork.api.models import formatAgent


class Plan(DjangoObjectType):
    scope = graphene.Field(lambda: types.Agent)
    planned = graphene.String(source='planned')
    due = graphene.String(source='due')
    note = graphene.String(source='note')

    class Meta:
        model = Order
        only_fields = ('id', 'name')


    plan_processes = graphene.List(lambda: types.Process)

    working_agents = graphene.List(lambda: types.Agent)


    def resolve_scope(self, args, *rargs):
        return formatAgent(self.provider)

    def resolve_plan_processes(self, args, context, info):
        return self.processes.all()

    def resolve_working_agents(self, args, context, info):
        return formatAgentList(self.all_working_agents())

