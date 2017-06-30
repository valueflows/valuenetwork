import faircoin_nrp.electrum_fair_nrp as efn

def is_connected():
    is_connected = efn.is_connected()
    if is_connected != 'ERROR':
        return is_connected
    else:
        return False

def network_fee():
    if not hasattr(efn, 'netfee') or not efn.netfee:
        network_fee = efn.network_fee()
        if network_fee != 'ERROR':
            efn.netfee = network_fee
            return network_fee
        else:
          efn.netfee = False
    else:
        return efn.netfee


def send_fake_faircoins(address_origin, address_end, amount):
    import time
    tx = str(time.time())
    broadcasted = True
    print "sent fake faircoins"
    return tx, broadcasted

def get_address_history(address):
    address_history = efn.get_address_history(address)
    if address_history != 'ERROR':
        return address_history

def get_address_balance(address):
    address_balance = efn.get_address_balance(address)
    if address_balance != 'ERROR':
        return address_balance

def is_valid(address):
    is_valid = efn.is_valid(address)
    if is_valid != 'ERROR':
        return is_valid

def get_confirmations(tx):
    confirmations = efn.get_confirmations(tx)
    if confirmations != 'ERROR':
        return confirmations
    else:
        return None, None

def get_transaction_info(tx_hash, address):
    transaction = efn.get_transaction(tx_hash)
    if transaction != 'ERROR':
        amount = 0
        for output in transaction['outputs']:
            if str(output['address']) == address:
                amount += int(output['value'])

        time = transaction['time']
        return (amount, time)
    else:
        return None, None

def is_mine(address):
    is_mine = efn.is_mine(address)
    if is_mine != 'ERROR':
        return is_mine
