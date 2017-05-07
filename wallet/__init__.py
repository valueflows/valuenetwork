from wallet.fairpay import FairpayGateway

def Factory(gateway):
    if gateway == "fairpay":
        return FairpayGateway.get()
