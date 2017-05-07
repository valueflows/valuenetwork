from wallet.interface import AbstractGateway

class FairpayGateway(AbstractGateway):

    @property
    def gateway_name(self):
        return 'fairpay'

    @property
    def currency(self):
        return 'euro'

    def get_balance(self, account):
        return "get_balance from " + str(account)

    def get_history(self, account):
        return "get_history from " + str(account)

    def send_funds(self):
        return "Error: this gateway is read-only"
