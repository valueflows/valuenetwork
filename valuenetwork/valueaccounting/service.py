import datetime
from decimal import *

from django.conf import settings
from django.core.exceptions import ValidationError

from valuenetwork.valueaccounting.models import (
    EconomicResource,
    EconomicResourceType,
    EventType,
    Transfer,
    TransferType,
    UseCase,
    ExchangeType,
    Exchange,
    EconomicEvent,
    AgentResourceRole,
    AgentResourceRoleType,
)

from faircoin import utils as faircoin_utils
from faircoin.models import FaircoinAddress, FaircoinTransaction

class ExchangeService(object):
    @classmethod
    def get(cls):
        return cls()

    @classmethod
    def faircoin_internal_exchange_type(cls):
        use_case = UseCase.objects.get(name="Internal Exchange")
        xt = ExchangeType.objects.filter(
            use_case=use_case,
            name="Transfer FairCoins")
        if xt:
            xt = xt[0]
        else:
            xt = ExchangeType(
                use_case=use_case,
                name="Transfer FairCoins")
            xt.save()
        return xt

    @classmethod
    def faircoin_internal_transfer_type(cls):
        xt = cls.faircoin_internal_exchange_type()
        tt = TransferType.objects.filter(
            exchange_type=xt,
            name="Transfer FairCoins")
        if tt:
            tt = tt[0]
        else:
            tt = TransferType(
                exchange_type=xt,
                name="Transfer FairCoins",
                sequence=1,
                is_currency=True,
            )
            tt.save()
        return tt

    @classmethod
    def faircoin_outgoing_exchange_type(cls):
        use_case = UseCase.objects.get(name="Outgoing Exchange")
        xt = ExchangeType.objects.filter(
            use_case=use_case,
            name="Send FairCoins")
        if xt:
            xt = xt[0]
        else:
            xt = ExchangeType(
                use_case=use_case,
                name="Send FairCoins")
            xt.save()
        return xt

    @classmethod
    def faircoin_outgoing_transfer_type(cls):
        xt = cls.faircoin_outgoing_exchange_type()
        tt = TransferType.objects.filter(
            exchange_type=xt,
            name="Send FairCoins")
        if tt:
            tt = tt[0]
        else:
            tt = TransferType(
                exchange_type=xt,
                name="Send FairCoins",
                sequence=1,
                is_currency=True,
            )
            tt.save()
        return tt

    @classmethod
    def faircoin_incoming_exchange_type(cls):
        use_case = UseCase.objects.get(name="Incoming Exchange")
        xt = ExchangeType.objects.filter(
            use_case=use_case,
            name="Receive FairCoins")
        if xt:
            xt = xt[0]
        else:
            xt = ExchangeType(
                use_case=use_case,
                name="Receive FairCoins")
            xt.save()
        return xt

    @classmethod
    def faircoin_incoming_transfer_type(cls):
        xt = cls.faircoin_incoming_exchange_type()
        tt = TransferType.objects.filter(
            exchange_type=xt,
            name="Receive FairCoins")
        if tt:
            tt = tt[0]
        else:
            tt = TransferType(
                exchange_type=xt,
                name="Receive FairCoins",
                sequence=1,
                is_currency=True,
            )
            tt.save()
        return tt


    def send_faircoins(self, from_agent, recipient, qty, resource, notes=None):
        if 'faircoin' not in settings.INSTALLED_APPS:
            return None
        to_resources = EconomicResource.objects.filter(faircoin_address__address=recipient)
        to_resource = None
        to_agent = None
        if to_resources:
            to_resource = to_resources[0]  # shd be only one
            to_agent = to_resource.owner()
        et_give = EventType.objects.get(name="Give")
        network_fee = faircoin_utils.network_fee()
        if to_resource and network_fee:
            tt = ExchangeService.faircoin_internal_transfer_type()
            xt = tt.exchange_type
            date = datetime.date.today()
            exchange = Exchange(
                exchange_type=xt,
                use_case=xt.use_case,
                name="Transfer Faircoins",
                start_date=date,
            )
            exchange.save()
            transfer = Transfer(
                transfer_type=tt,
                exchange=exchange,
                transfer_date=date,
                name="Transfer Faircoins",
            )
            transfer.save()
        else:
            tt = ExchangeService.faircoin_outgoing_transfer_type()
            xt = tt.exchange_type
            date = datetime.date.today()
            exchange = Exchange(
                exchange_type=xt,
                use_case=xt.use_case,
                name="Send Faircoins",
                start_date=date,
            )
            exchange.save()
            transfer = Transfer(
                transfer_type=tt,
                exchange=exchange,
                transfer_date=date,
                name="Send Faircoins",
            )
            transfer.save()

        state = "new"
        event = EconomicEvent(
            event_type=et_give,
            event_date=date,
            from_agent=from_agent,
            to_agent=to_agent,
            resource_type=resource.resource_type,
            resource=resource,
            quantity=qty,
            transfer=transfer,
            event_reference=recipient,
        )
        event.save()
        fairtx = FaircoinTransaction(
            event=event,
            tx_state=state,
            to_address=recipient,
        )
        fairtx.save()

        if to_resource:
            # network_fee is subtracted from quantity
            # so quantity is correct for the giving event
            # but receiving event will get quantity - network_fee
            quantity = qty - Decimal(float(network_fee) / 1.e6)
            et_receive = EventType.objects.get(name="Receive")
            event = EconomicEvent(
                event_type=et_receive,
                event_date=date,
                from_agent=from_agent,
                to_agent=to_agent,
                resource_type=to_resource.resource_type,
                resource=to_resource,
                quantity=quantity,
                transfer=transfer,
                event_reference=recipient,
            )
            event.save()
            fairtx = FaircoinTransaction(
                event=event,
                tx_state=state,
                to_address=recipient,
            )
            fairtx.save()

        return exchange

    def include_blockchain_tx_as_event(self, agent, resource):
        if 'faircoin' not in settings.INSTALLED_APPS:
            return []
        faircoin_address = str(resource.faircoin_address.address)
        tx_in_blockchain = faircoin_utils.get_address_history(faircoin_address)
        if not tx_in_blockchain: # Something wrong in daemon or network.
            return []

        event_list = resource.events.all()
        tx_in_ocp = []
        for event in event_list:
            tx_in_ocp.append(str(event.faircoin_transaction.tx_hash))

        tx_included = []
        for tx in tx_in_blockchain:
            if str(tx[0]) not in tx_in_ocp:
                amount, time = faircoin_utils.get_transaction_info(str(tx[0]), faircoin_address)
                confirmations, timestamp = faircoin_utils.get_confirmations(str(tx[0]))
                if amount and confirmations:
                    qty=Decimal(amount)/Decimal(1000000)
                    date = datetime.date.fromtimestamp(time)
                    tt = ExchangeService.faircoin_incoming_transfer_type()
                    xt = tt.exchange_type
                    exchange = Exchange(
                        exchange_type=xt,
                        use_case=xt.use_case,
                        name="Receive Faircoins",
                        start_date=date,
                    )
                    exchange.save()
                    transfer = Transfer(
                        transfer_type=tt,
                        exchange=exchange,
                        transfer_date=date,
                        name="Receive Faircoins",
                    )
                    transfer.save()

                    et_receive = EventType.objects.get(name="Receive")
                    state = "external"
                    if confirmations > 0:
                        state = "broadcast"
                    if confirmations > 2:
                        state = "confirmed"

                    event = EconomicEvent(
                        event_type=et_receive,
                        event_date=date,
                        to_agent=agent,
                        resource_type=resource.resource_type,
                        resource=resource,
                        quantity=qty,
                        transfer=transfer,
                        event_reference=faircoin_address
                    )
                    event.save()
                    fairtx = FaircoinTransaction(
                        event=event,
                        tx_hash=str(tx[0]),
                        tx_state=state,
                        to_address=faircoin_address,
                    )
                    fairtx.save()
                    tx_included.append(str(tx[0]))
        return tx_included

    def create_faircoin_resource(self, agent, address):
        if 'faircoin' not in settings.INSTALLED_APPS:
            return None
        role_types = AgentResourceRoleType.objects.filter(is_owner=True)
        owner_role_type = None
        if role_types:
            owner_role_type = role_types[0]
        resource_types = EconomicResourceType.objects.filter(
            behavior="dig_acct")
        if resource_types.count() == 0:
            raise ValidationError("Cannot create digital currency resource for " + agent.nick + " because no digital currency account ResourceTypes.")
            return None
        if resource_types.count() > 1:
            raise ValidationError("Cannot create digital currency resource for " + agent.nick + ", more than one digital currency account ResourceTypes.")
            return None
        resource_type = resource_types[0]
        if owner_role_type:
            # resource type has unit
            va = EconomicResource(
                resource_type=resource_type,
                identifier="Faircoin Ocp Account for " + agent.nick,
            )
            va.save()
            fairaddress = FaircoinAddress(
                resource=va,
                address=address,
            )
            fairaddress.save()
            arr = AgentResourceRole(
                agent=agent,
                role=owner_role_type,
                resource=va,
            )
            arr.save()
            return va
        else:
            raise ValidationError("Cannot create digital currency resource for " + agent.nick + " because no owner AgentResourceRoleTypes.")
            return None
