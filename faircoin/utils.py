import requests, json, logging
from random import randint
from logging.handlers import TimedRotatingFileHandler

from django.conf import settings

def init_logger():
    logger = logging.getLogger("faircoin")
    logger.setLevel(logging.WARNING)
    fhpath = "/".join([settings.PROJECT_ROOT, "faircoin/faircoin.log",])
    fh = TimedRotatingFileHandler(fhpath, when="d", interval=1, backupCount=7)
    fh.setLevel(logging.DEBUG)
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

# Get the network fee
def network_fee():
    response = send_command('fee', '')
    return response

# Stop electrum
def do_stop():
    response = send_command('do_stop', '')
    return response

# get the total balance for the wallet
# Returns a tupla with 3 values: Confirmed, Unmature, Unconfirmed
def get_balance():
    response = send_command('get_balance', '')
    return response

# get the balance for a determined address
# Returns a tupla with 3 values: Confirmed, Unmature, Unconfirmed
def get_address_balance(address):
    format_dict = [address]
    response = send_command('get_address_balance', format_dict)
    return response

#check if an address is valid
def is_valid(address):
    format_dict = [address]
    response = send_command('is_valid', format_dict)
    return response

#check if an address is from the wallet
def is_mine(address):
    format_dict = [address]
    response = send_command('is_mine', format_dict)
    return response

#read the history of an address
def get_address_history(address):
    format_dict = [address]
    response = send_command('get_address_history', format_dict)
    return response

# make a transfer from an adress of the wallet
def make_transaction_from_address(address_origin, address_end, amount):
    format_dict = [address_origin, address_end, amount]
    response = send_command('make_transaction_from_address', format_dict)
    return response

def address_history_info(address, page = 0, items = 20):
    format_dict = [address, page, items]
    response = send_command('address_history_info', format_dict)
    return response

# create new address for users or any other entity
def new_fair_address(entity_id, entity = 'generic'):
    format_dict = [entity_id, entity]
    response = send_command('new_fair_address', format_dict)
    return response

def get_confirmations(tx):
    format_dict = [tx]
    response = send_command('get_confirmations', format_dict)
    return response

def get_transaction(tx_hash):
    format_dict = [tx_hash]
    response = send_command('get_transaction', format_dict)
    return response

#Check if it is connected to the electum network
def is_connected():
    response = send_command('is_connected', '')
    return response

#Check if daemon is up and connected.
def daemon_is_up():
    response = send_command('daemon_is_up', '')
    return response

#get wallet info.
def get_wallet_info():
     response = send_command('get_wallet_info', '')
     return response

#import private key and label address
def import_key(privkey, entity_id, entity = 'generic'):
    format_dict = [privkey, entity_id, entity]
    response = send_command('import_key', format_dict)
    return response
