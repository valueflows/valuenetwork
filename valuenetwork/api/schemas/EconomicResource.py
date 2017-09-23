#
# Graphene schema for exposing EconomicResource model
#

import graphene
from valuenetwork.valueaccounting.models import EconomicResource as EconomicResourceProxy
from valuenetwork.api.types.EconomicResource import EconomicResource


class Query(graphene.AbstractType):

    # define input query params

    economic_resource = graphene.Field(EconomicResource,
                                       id=graphene.Int())

    all_economic_resources = graphene.List(EconomicResource)

    # resolve methods

    def resolve_economic_resource(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            resource = EconomicResourceProxy.objects.get(pk=id)
            if resource:
                #resource.current_quantity = self._current_quantity(quantity=resource.quantity, unit=resource.unit)
                return resource
        return None   

    def resolve_all_economic_resources(self, args, context, info):
        resources = EconomicResourceProxy.objects.all()
        #for resource in resources:
            #resource.current_quantity = self._current_quantity(quantity=resource.quantity, unit=resource.unit)
        return resources
'''
class CreateEconomicResource(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        name = graphene.String(required=True)
        planned_start = graphene.String(required=True)
        planned_duration = graphene.Int(required=True)
        scope_id = graphene.Int(required=True)
        note = graphene.String(required=False)

    economic_resource = graphene.Field(lambda: EconomicResource)

    @classmethod
    def mutate(cls, root, args, context, info):
        #import pdb; pdb.set_trace()
        name = args.get('name')
        planned_start = args.get('planned_start')
        planned_duration = args.get('planned_duration')
        note = args.get('note')
        scope_id = args.get('scope_id')

        if not note:
            note = ""
        start_date = datetime.datetime.strptime(planned_start, '%Y-%m-%d').date()
        end_date = start_date + datetime.timedelta(days=planned_duration)
        scope = EconomicAgent.objects.get(pk=scope_id)
        process = ProcessProxy(
            name=name,
            start_date=start_date,
            end_date=end_date,
            notes=note,
            context_agent=scope,
            created_by=context.user,
        )
        economic_resource.save()

        return CreateProcess(economic_resource=economic_resource)


class UpdateProcess(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)
        name = graphene.String(required=False)
        planned_start = graphene.String(required=False)
        planned_duration = graphene.Int(required=False)
        scope_id = graphene.Int(required=False)
        note = graphene.String(required=False)
        is_finished = graphene.Boolean(required=False)

    process = graphene.Field(lambda: Process)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        name = args.get('name')
        planned_start = args.get('planned_start')
        planned_duration = args.get('planned_duration')
        note = args.get('note')
        scope_id = args.get('scope_id')
        is_finished = args.get('is_finished')

        process = ProcessProxy.objects.get(pk=id)
        if process:
            if name:
                process.name = name
            if note:
                process.notes=note
            if planned_start:
                start_date = datetime.datetime.strptime(planned_start, '%Y-%m-%d').date()
                process.start_date=start_date
            if planned_duration:
                end_date = process.start_date + datetime.timedelta(days=planned_duration)
                process.end_date=end_date
            if scope_id:
                scope = EconomicAgent.objects.get(pk=scope_id)
                process.context_agent=scope
            if is_finished:
                process.finished=is_finished
            process.changed_by=context.user
            process.save_api()

        return UpdateProcess(process=process)


class DeleteProcess(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)

    process = graphene.Field(lambda: Process)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        process = ProcessProxy.objects.get(pk=id)
        if process:
            if process.is_deletable():
                process.delete()
                #TODO: add logic for adjusting other processes if workflow plan
            else:
                raise PermissionDenied("Process has economic events so cannot be deleted.")

        return DeleteProcess(process=process)
'''