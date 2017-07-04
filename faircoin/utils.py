import requests, json, logging, time
from random import randint
from logging.handlers import TimedRotatingFileHandler

from django.conf import settings

def init_logger():
    logger = logging.getLogger("faircoin")
    logger.setLevel(logging.INFO)
    fhpath = "/".join([settings.PROJECT_ROOT, "faircoin/faircoin.log",])
    fh = TimedRotatingFileHandler(fhpath, when="d", interval=1, backupCount=7)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

url = "http://localhost:8069"
timeout = 7
logger = init_logger()

# Send command to the daemon.
def send_command(cmd, params):
    if params == '': params = []
    random_id = randint(1,10000)
    headers = {'content-type': 'application/json'}
    data = json.dumps({'method': cmd, 'params': params, 'jsonrpc': '2.0', 'id': random_id })
    logger.debug('Command: %s (params: %s)' %(cmd, params))

    try:
        response = requests.post(url, headers=headers, data=data, timeout=timeout)
    except requests.exceptions.ConnectionError as e:
        logger.error("Cannot connect to faircoin daemon: %s" % e)
        return "ERROR"
    except requests.exceptions.Timeout as e:
        logger.error("Timeout connecting to faircoin daemon: %s" % e)
        return "ERROR"

    try:
        r = response.json()
        if int(response.status_code) == 200:
            logger.debug('Response: %s' %(r['result']))
            out = r['result']
        else:
            out = 'ERROR'
    except:
        out = 'ERROR'

    return out

# Check if wallet is connected to the electum network.
def is_connected():
    response = send_command('is_connected', '')
    if response == 'ERROR':
        return False
    else:
        return response

# Get the network fee.
def network_fee():
    response = send_command('fee', '')
    if response == 'ERROR':
        return False
    else:
        return response

# A mock function for tests in valueaccounting app.
def send_fake_faircoins(address_origin, address_end, amount):
    tx = str(time.time())
    broadcasted = True
    print "sent fake faircoins"
    return tx, broadcasted

# Get the balance for a determined address
# Returns a tupla with 3 values: Confirmed, Unmature, Unconfirmed
def get_address_balance(address):
    format_dict = [address]
    response = send_command('get_address_balance', format_dict)
    if response != 'ERROR':
        return response

# Gets the transactions history of an address
def get_address_history(address):
    format_dict = [address]
    response = send_command('get_address_history', format_dict)
    if response != 'ERROR':
        return response

# Check if an address is valid
def is_valid(address):
    format_dict = [address]
    response = send_command('is_valid', format_dict)
    if response != 'ERROR':
        return response

# Check if an address belongs to the wallet
def is_mine(address):
    format_dict = [address]
    response = send_command('is_mine', format_dict)
    if response != 'ERROR':
        return response

# Get the confirmations in the faircoin network of a transaction.
def get_confirmations(tx):
    format_dict = [tx]
    response = send_command('get_confirmations', format_dict)
    if response != 'ERROR':
        return response
    else:
        return None, None

# Gets the transaction amount and created time from tx hash and output address.
def get_transaction_info(tx_hash, address):
    format_dict = [tx_hash]
    transaction = send_command('get_transaction', format_dict)
    if transaction != 'ERROR':
        amount = 0
        for output in transaction['outputs']:
            if str(output['address']) == address:
                amount += int(output['value'])

        time = transaction['time']
        return (amount, time)
    else:
        return None, None

# make a transfer from an adress of the wallet
def make_transaction_from_address(address_origin, address_end, amount):
    format_dict = [address_origin, address_end, amount]
    response = send_command('make_transaction_from_address', format_dict)
    return response

# create a new labeled address
def new_fair_address(entity_id, entity = 'generic'):
    format_dict = [entity_id, entity]
    response = send_command('new_fair_address', format_dict)
    return response

#import private key and label address
def import_key(privkey, entity_id, entity = 'generic'):
    format_dict = [privkey, entity_id, entity]
    response = send_command('import_key', format_dict)
    return response
