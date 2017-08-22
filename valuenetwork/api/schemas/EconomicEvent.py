#
# Graphene schema for exposing EconomicEvent
#

import graphene
import datetime
from decimal import Decimal
from valuenetwork.valueaccounting.models import EconomicEvent as EconomicEventProxy, Commitment
from valuenetwork.api.types.EconomicEvent import EconomicEvent, Action
from valuenetwork.api.models import Fulfillment
from six import with_metaclass
from django.contrib.auth.models import User
from .Auth import AuthedInputMeta, AuthedMutation
from django.core.exceptions import PermissionDenied


class Query(graphene.AbstractType):

    # define input query params

    economic_event = graphene.Field(EconomicEvent,
                                    id=graphene.Int())

    all_economic_events = graphene.List(EconomicEvent)

    # resolvers

    def resolve_economic_event(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            event = EconomicEventProxy.objects.get(pk=id)
            if event:
                return event
        return None

    def resolve_all_economic_events(self, args, context, info):
        return EconomicEventProxy.objects.all()


class CreateEconomicEvent(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        action = graphene.String(required=True)
        process_id = graphene.Int(required=False)
        provider_id = graphene.Int(required=False)
        receiver_id = graphene.Int(required=False)
        scope_id = graphene.Int(required=False)
        #affected_taxonomy_item_id = graphene.Int(required=True)
        affected_resource_id = graphene.Int(required=False)
        affected_numeric_value = graphene.String(required=True)
        affected_unit_id = graphene.Int(required=True)
        start = graphene.String(required=False)
        note = graphene.String(required=False)

    economic_event = graphene.Field(lambda: EconomicEvent)

    @classmethod
    def mutate(cls, root, args, context, info):
        action = args.get('action')
        process_id = args.get('process_id')
        provider_id = args.get('provider_id')
        receiver_id = args.get('receiver_id')
        scope_id = args.get('scope_id')
        #affected_taxonomy_item_id = args.get('committed_taxonomy_item_id')
        affected_resource_id = args.get('affected_resource_id')
        committed_numeric_value = args.get('committed_numeric_value')
        affected_unit_id = args.get('affected_unit_id')
        start = args.get('start')
        note = args.get('note')

        event_type = EventType.objects.convert_action_to_event_type(action)
        if not note:
            note = ""
        if start:
            start = datetime.datetime.strptime(planned_start, '%Y-%m-%d').date()
        if scope_id:
            scope = EconomicAgent.objects.get(pk=scope_id)
        else:
            scope = None
        if provider_id:
            provider = EconomicAgent.objects.get(pk=provider_id)
        else:
            provider = None
        if receiver_id:
            receiver = EconomicAgent.objects.get(pk=receiver_id)
        else:
            receiver = None
        if process_id:
            process = Process.objects.get(pk=process_id)
        else:
            process = None
       #if committed_taxonomy_item_id:
       #     committed_taxonomy_item = EconomicResourceType.objects.get(pk=committed_taxonomy_item_id)
       # else:
       #     committed_taxonomy_item = None
        if affected_resource_id:
            affected_resource = EconomicResource.objects.get(pk=affected_resource_id)
        else:
            affected_resource = None
        affected_unit = Unit.objects.get(pk=affected_unit_id)

        economic_event = EconomicEventProxy(
            event_type = event_type,
            process = process,
            from_agent = provider,
            to_agent = receiver,
            resource_type = committed_taxonomy_item,
            resource = committed_resource,
            quantity = Decimal(committed_numeric_value),
            unit_of_quantity = committed_unit,
            start_date = planned_start,
            description=note,
            context_agent=scope,
            created_by=context.user,
        )
        economic_event.save()

        return CreateEconomicEvent(economic_event=economic_event)


class UpdateEconomicEvent(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)
        action = graphene.String(required=False)
        process_id = graphene.Int(required=False)
        provider_id = graphene.Int(required=False)
        receiver_id = graphene.Int(required=False)
        scope_id = graphene.Int(required=False)
        #affected_taxonomy_item_id = graphene.Int(required=True)
        affected_resource_id = graphene.Int(required=False)
        affected_numeric_value = graphene.String(required=True)
        affected_unit_id = graphene.Int(required=True)
        start = graphene.String(required=False)
        note = graphene.String(required=False)

    economic_event = graphene.Field(lambda: EconomicEvent)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        action = args.get('action')
        process_id = args.get('process_id')
        provider_id = args.get('provider_id')
        receiver_id = args.get('receiver_id')
        scope_id = args.get('scope_id')
        #affected_taxonomy_item_id = args.get('committed_taxonomy_item_id')
        affected_resource_id = args.get('affected_resource_id')
        committed_numeric_value = args.get('committed_numeric_value')
        affected_unit_id = args.get('affected_unit_id')
        start = args.get('start')
        note = args.get('note')

        economic_event = EconomicEventProxy.objects.get(pk=id)
        if economic_event:
            if action:
                economic_event.event_type = EventType.objects.convert_action_to_event_type(action)
            if note:
                economic_event.description = note
            if planned_start:
                economic_event.start_date = datetime.datetime.strptime(planned_start, '%Y-%m-%d').date()
            if scope_id:
                economic_event.context_agent = EconomicAgent.objects.get(pk=scope_id)
            if provider_id:
                economic_event.from_agent = EconomicAgent.objects.get(pk=provider_id)
            if receiver_id:
                economic_event.to_agent = EconomicAgent.objects.get(pk=receiver_id)
            if process_id:
                economic_event.process = Process.objects.get(pk=process_id)
            #if committed_taxonomy_item_id:
            #    economic_event.resource_type = EconomicResourceType.objects.get(pk=committed_taxonomy_item_id)
            if affected_resource_id:
                economic_event.resource = EconomicResource.objects.get(pk=affected_resource_id)
            if affected_numeric_value:
                economic_event.quantity = Decimal(affected_numeric_value)
            if affected_unit_id:
                economic_event.unit_of_quantity = Unit.objects.get(pk=affected_unit_id)

            economic_event.save()

        return UpdateEconomicEvent(economic_event=economic_event)


class DeleteEconomicEvent(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        id = graphene.Int(required=True)

    economic_event = graphene.Field(lambda: EconomicEvent)

    @classmethod
    def mutate(cls, root, args, context, info):
        id = args.get('id')
        economic_event = EconomicEventProxy.objects.get(pk=id)
        if economic_event:
            economic_event.delete()

        return DeleteEconomicEvent(economic_event=economic_event)
