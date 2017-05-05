import faircoin_nrp.electrum_fair_nrp as efn

def init_electrum_fair():
    try:
        daemon = efn.daemon_is_up()
    except:
        msg = "Cannot connect with daemon. Exiting."
        assert False, msg

    if not daemon or (daemon is 'ERROR'):
        return False

    try:
        network = efn.is_connected()
    except:
        msg = "Cannot connect with electrum-server. Exiting."
        assert False, msg

    return network and (network is not 'ERROR')

def network_fee():
    if init_electrum_fair():
        return efn.network_fee()

def send_fake_faircoins(address_origin, address_end, amount):
    import time
    tx = str(time.time())
    broadcasted = True
    print "sent fake faircoins"
    return tx, broadcasted

def get_address_history(address):
    if init_electrum_fair():
        return efn.get_address_history(address)

def get_address_balance(address):
    if init_electrum_fair():
        return efn.get_address_balance(address)

def is_valid(address):
    if init_electrum_fair():
        return efn.is_valid(address)

def get_confirmations(tx):
    if init_electrum_fair():
        return efn.get_confirmations(tx)
    else:
        return None, None

def get_transaction_info(tx_hash, address):
    if init_electrum_fair():
        transaction = efn.get_transaction(tx_hash)
        amount = 0
        for output in transaction['outputs']:
            if str(output['address']) == address:
                amount += int(output['value'])

        time = transaction['time']
        return (amount, time)

def is_mine(address):
    if init_electrum_fair():
        return efn.is_mine(address)
