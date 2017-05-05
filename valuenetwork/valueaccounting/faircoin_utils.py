import faircoin_nrp.electrum_fair_nrp as efn

def init_electrum_fair():
    try:
        assert(efn.daemon_is_up())
    except:
        msg = "Cannot connect with daemon. Exiting."
        assert False, msg
    try:
        assert(efn.is_connected())
    except:
        msg = "Cannot connect with electrum-server. Exiting."
        assert False, msg
#obsolete
"""
def create_address_for_agent(agent):
    init_electrum_fair()
    wallet = efn.wallet
    address = None
    address = efn.new_fair_address(
        entity_id = agent.nick,
        entity = agent.agent_type.name,
        )
    return address
"""

def network_fee():
    return efn.network_fee()

def send_fake_faircoins(address_origin, address_end, amount):
    import time
    tx = str(time.time())
    broadcasted = True
    print "sent fake faircoins"
    return tx, broadcasted

def get_address_history(address):
    init_electrum_fair()
    return efn.get_address_history(address)

def get_address_balance(address):
    init_electrum_fair()
    return efn.get_address_balance(address)

def is_valid(address):
    init_electrum_fair()
    return efn.is_valid(address)

def get_confirmations(tx):
    init_electrum_fair()
    return efn.get_confirmations(tx)

def get_transaction_info(tx_hash, address):
    init_electrum_fair()
    transaction = efn.get_transaction(tx_hash)
    amount = 0
    for output in transaction['outputs']:
        if str(output['address']) == address:
            amount += int(output['value'])

    time = transaction['time']
    return (amount, time)

def is_mine(address):
    init_electrum_fair()
    return efn.is_mine(address)
