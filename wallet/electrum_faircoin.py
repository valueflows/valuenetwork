from wallet.interface import AbstractGateway
from wallet import electrum_faircoin_utils as efu

class ElectrumFaircoinGateway(AbstractGateway):

    @property
    def gateway_name(self):
        return 'electrum_faircoin'

    @property
    def currency(self):
        return 'faircoin'

    def get_balance(self, account):
        return "get_balance from " + str(account)

    def get_history(self, account):
        return "get_history from " + str(account)

    def send_funds(self, account):
        return "send_funds from " + str(account)
