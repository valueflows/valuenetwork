import sys
import time
import logging
from decimal import *

logger = logging.getLogger("faircoin_cron.process")

from django.conf import settings
from django.db.models import Q

import faircoin.utils as efn

from valuenetwork.valueaccounting.models import EconomicAgent, EconomicEvent, EconomicResource
from valuenetwork.valueaccounting.lockfile import FileLock, AlreadyLocked, LockTimeout, LockFailed

#FAIRCOIN_DIVISOR = int(1000000)

def acquire_lock():
    lock = FileLock("broadcast-faircoins")
    logger.debug("acquiring lock...")
    try:
        #lock.acquire(settings.BROADCAST_FAIRCOINS_LOCK_WAIT_TIMEOUT)
        lock.acquire(1)
    except AlreadyLocked:
        logger.warning("lock already in place. quitting.")
        return False
    except LockTimeout:
        logger.warning("waiting for the lock timed out. quitting.")
        return False
    logger.debug("lock acquired.")
    return lock

def create_address_from_file(entity_id, entity):
    filename = settings.NEW_FAIRCOIN_ADDRESSES_FILE
    address = None
    logger.info("About import privkey for " + str(entity) + ": " + str(entity_id))
    with open(filename, 'r') as fin:
        try:
            data = fin.read().splitlines(True)
            address_in_file, privkey = data[0].strip().split(',')
        except:
            logger.critical("Error reading new faircoin addresses file.")
            return None
    try:
        status, address = efn.import_key(privkey, entity_id, entity)
    except:
        logger.critical("Error importing key: " + address)
        return None
    if status == 'ERROR':
        logger.critical("Error importing key: " + address)
        return None
    if address != address_in_file:
        logger.warning("Address returned on importing key is different from the file one.")
    with open(filename, 'w') as fout:
        try:
           fout.writelines(data[1:])
        except:
           logger.critical("Error writting new faircoin addresses file.")
    logger.info("Private key succesfully imported to wallet for "
        + str(entity) + ": " + str(entity_id) + " (address: " + address + ")")
    return address

def create_address_for_agent(agent):
    address = None
    if hasattr(settings, 'NEW_FAIRCOIN_ADDRESSES_FILE'):
        address = create_address_from_file(
            entity_id = agent.nick.encode('ascii','ignore'),
            entity = agent.agent_type.name,
            )
        return address
    if efn.is_connected():
        try:
            address = efn.new_fair_address(
                entity_id = agent.nick.encode('ascii','ignore'),
                entity = agent.agent_type.name,
                )
        except Exception:
            _, e, _ = sys.exc_info()
            logger.critical("an exception occurred in creating a FairCoin address: {0}".format(e))

        if (address is not None) and (address != 'ERROR'):
            used = EconomicResource.objects.filter(faircoin_address__address=address)
            if used.count():
                msg = " ".join(["address already existent! (count[0]=", str(used[0]), ") when creating new address for", agent.name])
                logger.critical(msg)
                return None #create_address_for_agent(agent)
        elif address == 'ERROR':
            msg = " ".join(["address string is ERROR. None returned. agent:", agent.name])
            logger.critical(msg)
            return None
    return address

def create_address_for_resource(resource):
    agent = resource.owner()
    address = create_address_for_agent(agent)
    if address:
        resource.faircoin_address.address = address
        resource.save()
        return True
    else:
        msg = " ".join(["Failed to get a FairCoin address for", agent.name])
        logger.warning(msg)
        return False

def create_requested_addresses():
    try:
        requests = EconomicResource.objects.filter(
            faircoin_address__address="address_requested")

        msg = " ".join(["new FairCoin address requests count:", str(requests.count())])
        logger.debug(msg)
    except Exception:
        _, e, _ = sys.exc_info()
        logger.critical("an exception occurred in retrieving FairCoin address requests: {0}".format(e))
        return "failed to get FairCoin address requests"

    if requests:
        if efn.is_connected():
            logger.debug("broadcast_tx ready to process FairCoin address requests")
            for resource in requests:
                result = create_address_for_resource(resource)

            msg = " ".join(["created", str(requests.count()), "new faircoin addresses."])
    else:
        msg = "No new faircoin address requests to process."
    return msg

def broadcast_tx():

    try:
        events = EconomicEvent.objects.filter(
            faircoin_transaction__tx_state="new").order_by('pk')
        events = events.filter(
            Q(event_type__name='Give')|Q(event_type__name='Distribution'))
        msg = " ".join(["new FairCoin event count:", str(events.count())])
        logger.debug(msg)
    except Exception:
        _, e, _ = sys.exc_info()
        logger.critical("an exception occurred in retrieving events: {0}".format(e))
        logger.warning("releasing lock because of error...")
        lock.release()
        logger.debug("released.")
        return "failed to get events"

    try:
        successful_events = 0
        failed_events = 0
        if events and efn.is_connected():
            logger.debug("broadcast_tx ready to process events")
            for event in events:
                if event.resource:
                    if event.event_type.name=="Give":
                        address_origin = event.resource.faircoin_address.address
                        address_end = event.faircoin_address.to_address
                    elif event.event_type.name=="Distribution":
                        address_origin = event.from_agent.faircoin_address()
                        address_end = event.resource.faircoin_address.address
                    fairtx = event.faircoin_transaction
                    amount = float(event.quantity) * 1.e6 # In satoshis
                    if amount < 1001:
                        fairtx.tx_state = "broadcast"
                        fairtx.tx_hash = "Null"
                        fairtx.save()
                        continue

                    logger.info("About to build transaction. Amount: %d" %(int(amount)))
                    tx_hash = None
                    try:
                        tx_hash = efn.make_transaction_from_address(address_origin, address_end, int(amount))
                    except Exception:
                        _, e, _ = sys.exc_info()
                        logger.critical("an exception occurred in make_transaction_from_address: {0}".format(e))

                    if (tx_hash == "ERROR") or (not tx_hash):
                        logger.warning("ERROR tx_hash, make tx failed without raising Exception")
                        failed_events += 1
                    elif tx_hash:
                        successful_events += 1
                        fairtx.tx_state = "broadcast"
                        fairtx.tx_hash = tx_hash
                        fairtx.save()
                        transfer = event.transfer
                        if transfer:
                            revent = transfer.receive_event()
                            if revent:
                                refairtx = revent.faircoin_transaction
                                refairtx.tx_state = "broadcast"
                                refairtx.tx_hash = tx_hash
                                refairtx.save()
                        msg = " ".join([ "Broadcasted tx", tx_hash, "amount", str(amount), "from", address_origin, "to", address_end ])
                        logger.info(msg)
    except Exception:
        _, e, _ = sys.exc_info()
        logger.critical("an exception occurred in processing events: {0}".format(e))
        return "failed to process events"

    if events:
        msg = " ".join(["Broadcast", str(successful_events), "new faircoin tx."])
        if failed_events:
            msg += " ".join([ str(failed_events), "events failed."])
    else:
        msg = "No new faircoin tx to process."
    return msg
