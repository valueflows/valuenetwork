#
# Graphene schema for exposing Transfer model

import graphene
import datetime
from decimal import Decimal

from valuenetwork.valueaccounting.models import Transfer as TransferProxy, EconomicEvent as EconomicEventProxy,  EconomicResource as EconomicResourceProxy, AgentResourceRoleType, AgentResourceRole, EventType, EconomicAgent, AgentUser
from valuenetwork.api.types.Exchange import Transfer
from six import with_metaclass
from django.contrib.auth.models import User
from .Auth import AuthedInputMeta, AuthedMutation
from django.core.exceptions import PermissionDenied


class Query(graphene.AbstractType):

    # define input query params

    transfer = graphene.Field(Transfer,
                              id=graphene.Int())

    all_transfers = graphene.List(Transfer)

    # load single item

    def resolve_transfer(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            transfer = TransferProxy.objects.get(pk=id)
            if transfer:
                return transfer
        return None

    # load all items

    def resolve_all_transfers(self, args, context, info):
        return TransferProxy.objects.all()


# doing this minimally for the LearnDeep requirement 2020 spring
class CreateTransfer(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        provider_id = graphene.Int(required=True)
        receiver_id = graphene.Int(required=True)
        affects_id = graphene.Int(required=True)
        receiver_affects_id = graphene.Int(required=False)
        affected_numeric_value = graphene.String(required=True)
        start = graphene.String(required=False)
        create_resource = graphene.Boolean(required=False)
        resource_image = graphene.String(required=False)
        resource_note = graphene.String(required=False)

    transfer = graphene.Field(lambda: Transfer)

    @classmethod
    def mutate(cls, root, args, context, info):
        provider_id = args.get('provider_id')
        receiver_id = args.get('receiver_id')
        affects_id = args.get('affects_id')
        receiver_affects_id = args.get('receiver_affects_id')
        affected_numeric_value = args.get('affected_numeric_value')
        start = args.get('start')
        create_resource = args.get('create_resource', False)
        resource_image = args.get('resource_image')
        resource_note = args.get('resource_note')
        #import pdb; pdb.set_trace()

        if start:
            start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
        else:
            start = datetime.date.today()
        provider = EconomicAgent.objects.get(pk=provider_id)
        receiver = EconomicAgent.objects.get(pk=receiver_id)
        affects = EconomicResourceProxy.objects.get(pk=affects_id)
        receiver_affects = None
        if receiver_affects_id:
            receiver_affects = EconomicResourceProxy.objects.get(pk=receiver_affects_id)
        if not receiver_affects:
            if create_resource:
                if not resource_note:
                    resource_note = affects.notes
                if not resource_image:
                    resource_image = affects.image
                receiver_affects = EconomicResourceProxy(
                    resource_type=affects.resource_type,
                    quantity=Decimal(affected_numeric_value),
                    photo_url=resource_image,
                    identifier=affects.identifier,
                    current_location=None,
                    notes=resource_note,
                    url="",
                    created_by=context.user,
                    #location
                )

        transfer = TransferProxy(
            name="Transfer item",
            transfer_date=start,
            notes="",
            context_agent=provider
        )
        give_et = EventType.objects.get(name="Give")
        give_event = EconomicEventProxy(
            event_type = give_et,
            process = None,
            from_agent = provider,
            to_agent = receiver,
            resource_type = affects.resource_type,
            resource = affects,
            quantity = Decimal(affected_numeric_value),
            unit_of_quantity = affects.resource_type.unit,
            event_date = start,
            description=resource_note,
            context_agent=provider,
            url="",
            commitment=None,
            is_contribution=False,
        )
        receive_et = EventType.objects.get(name="Receive")
        receive_event = EconomicEventProxy(
            event_type = receive_et,
            process = None,
            from_agent = provider,
            to_agent = receiver,
            resource_type = affects.resource_type,
            quantity = Decimal(affected_numeric_value),
            unit_of_quantity = affects.resource_type.unit,
            event_date = start,
            description=resource_note,
            context_agent=receiver,
            url="",
            commitment=None,
            is_contribution=False,
        )

        #import pdb; pdb.set_trace()
        user_agent = AgentUser.objects.get(user=context.user).agent
        is_authorized = user_agent.is_authorized(object_to_mutate=give_event)
        if is_authorized:
            transfer.save_api()
            give_event.transfer = transfer
            give_event.save_api(user=context.user, create_resource=False)
            if receiver_affects:
                receiver_affects.save()
                receive_event.resource = receiver_affects
            receive_event.transfer = transfer
            receive_event.save_api(user=context.user, create_resource=create_resource)
            if create_resource:
                roles = AgentResourceRoleType.objects.filter(is_owner=True)
                if roles and receiver:
                    owner_role = roles[0]
                    arr = AgentResourceRole(
                        agent=receiver,
                        resource=receiver_affects,
                        role=owner_role,
                    )
                    arr.save()
        else:
            raise PermissionDenied('User not authorized to perform this action.')

        return CreateTransfer(transfer=transfer)
