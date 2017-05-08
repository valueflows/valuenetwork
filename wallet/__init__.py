from wallet.electrum_faircoin import ElectrumFaircoinGateway
from wallet.fairpay import FairpayGateway

def Factory(gateway):
    if gateway == "electrum_faircoin":
        return ElectrumFaircoinGateway.get()
    elif gateway == "fairpay":
        return FairpayGateway.get()
