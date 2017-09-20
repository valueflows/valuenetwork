#
# Graphene schema for exposing Plan (Order) model
#

import graphene
import datetime
from valuenetwork.valueaccounting.models import Order, EconomicAgent
from valuenetwork.api.types.Plan import Plan
from six import with_metaclass
from django.contrib.auth.models import User
from .Auth import AuthedInputMeta, AuthedMutation
from django.core.exceptions import PermissionDenied


class Query(graphene.AbstractType):

    plan = graphene.Field(Plan,
                          id=graphene.Int())

    all_plans = graphene.List(Plan)

    # load single item

    def resolve_plan(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            plan = Order.objects.get(pk=id)
            if plan:
                return plan
        return None

    # load all items

    def resolve_all_plans(self, args, context, info):
        return Order.objects.rand_orders()


class CreatePlan(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        name = graphene.String(required=True)
        due = graphene.String(required=True)
        note = graphene.String(required=False)

    plan = graphene.Field(lambda: Plan)

    @classmethod
    def mutate(cls, root, args, context, info):
        name = args.get('name')
        due = args.get('due')
        note = args.get('note')

        if not note:
            note = ""
        due = datetime.datetime.strptime(due, '%Y-%m-%d').date()
        plan = Order(
            order_type="rand",
            name=name,
            due_date=due,
            description=note,
            created_by=context.user,
        )
        plan.save()

        return CreatePlan(plan=plan)


class UpdatePlan(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)
        name = graphene.String(required=False)
        due = graphene.String(required=False)
        note = graphene.String(required=False)

    plan = graphene.Field(lambda: Plan)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        name = args.get('name')
        due = args.get('due')
        note = args.get('note')

        plan = Order.objects.get(pk=id)
        if plan:
            if name:
                plan.name = name
            if note:
                plan.description=note
            if due:
                due_date = datetime.datetime.strptime(due, '%Y-%m-%d').date()
                plan.due_date=due_date
            plan.save()

        return UpdatePlan(plan=plan)


class DeletePlan(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)

    plan = graphene.Field(lambda: Plan)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        plan = Order.objects.get(pk=id)
        if plan:
            procs = plan.unordered_processes()
            if len(procs) == 0: #TODO is this the right requirement? >> no, there is a bunch of code in the view!
                plan.delete()
            else:
                raise PermissionDenied("Plan has processes so cannot be deleted.")

        return DeletePlan(plan=plan)
