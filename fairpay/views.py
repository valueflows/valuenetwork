from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404

from fairpay.models import FairpayOauth2
from fairpay.forms import FairpayOauth2Form
from fairpay.utils import FairpayOauth2Connection

@login_required
def start(request, agent_id):
    try:
        oauth = FairpayOauth2.objects.filter(agent=agent_id)
    except ObjectDoesNotExist:
        return redirect('fairpay_auth', agent_id=agent_id)

    if oauth.count() == 1:
        return redirect('fairpay_history', agent_id=agent_id)
    elif oauth.count() > 1:
        # TODO: several fairpay accounts for one agent
        pass


@login_required
def auth(request, agent_id):
    if request.method == 'POST':
        form = FairpayOauth2Form(request.POST)
        if form.is_valid():
            # TODO: call API for new access_token and save
            return redirect('fairpay_history', agent_id=agent_id)

    else:
        form = FairpayOauth2Form()

    return render(request, 'fairpay_auth.html', {'form': form})

@login_required
def history(request, agent_id):
    # TODO: check current access_token, redirect or list transactions
