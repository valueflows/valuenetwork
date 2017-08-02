#
# Graphene schema for exposing Process model
#
# @package: OCP
# @since:   2017-06-22
#

#from django.core.exceptions import PermissionDenied

import graphene
import datetime
from valuenetwork.valueaccounting.models import Process as ProcessProxy, EconomicAgent
from valuenetwork.api.types.Process import Process
from django.contrib.auth.models import User


class Query(graphene.AbstractType):

    # define input query params

    process = graphene.Field(Process,
                            id=graphene.Int())

    all_processes = graphene.List(Process)

    # load single item

    def resolve_process(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            process = ProcessProxy.objects.get(pk=id)
            if process:
                return process
        return None

    # load all items

    def resolve_all_processes(self, args, context, info):
        return ProcessProxy.objects.all()


class CreateProcess(graphene.Mutation):
    class Input:
        name = graphene.String(required=True)
        planned_start = graphene.String(required=True)
        planned_duration = graphene.Int(required=True)
        scope_id = graphene.Int(required=True)
        note = graphene.String(required=False)
        created_by_id = graphene.Int(required=True)

    process = graphene.Field(lambda: Process)

    @classmethod
    def mutate(cls, root, args, context, info):
        name = args.get('name')
        planned_start = args.get('planned_start')
        planned_duration = args.get('planned_duration')
        note = args.get('note')
        scope_id = args.get('scope_id')
        created_by_id = args.get('created_by_id')

        if not note:
            note = ""
        start_date = datetime.datetime.strptime(planned_start, '%Y-%m-%d').date()
        end_date = start_date + datetime.timedelta(days=planned_duration)
        scope = EconomicAgent.objects.get(pk=scope_id)
        created_by = User.objects.get(pk=created_by_id)
        process = ProcessProxy(
            name=name,
            start_date=start_date,
            end_date=end_date,
            notes=note,
            context_agent=scope,
            created_by=created_by,
            )
        process.save()

        return CreateProcess(process=process)
