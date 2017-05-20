from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from valuenetwork.valueaccounting.models import EconomicAgent
from fairpay.models import FairpayOauth2
from fairpay.forms import FairpayOauth2Form
from fairpay.utils import FairpayOauth2Error, FairpayOauth2Connection

@login_required
def start(request, agent_id):
    #TODO: check if current user can manage this agent.
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
    #TODO: check if current user can manage this agent.
    if request.method == 'POST':
        form = FairpayOauth2Form(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            c = FairpayOauth2Connection.get()
            try:
                data = c.new_token(name, password)
            except FairpayOauth2Error:
                raise ValidationError('Authentication failed.')
                #TODO: handle fail here. Message to user.
            try:
                agent = EconomicAgent.objects.get(id=agent_id)
                FairpayOauth2.objects.create(
                    agent = agent,
                    fairpay_user = name,
                    access_token = data['access_token'],
                    refresh_token = data['refresh_token'],
                    expires_token = int(data['expires_in']),
                )
            except:
                pass
                #TODO: handle fail here.
            return redirect('fairpay_history', agent_id=agent_id)

    else:
        form = FairpayOauth2Form()

    return render(request, 'fairpay_auth.html', {'oauth_form': form})

@login_required
def history(request, agent_id):
    #TODO: check if current user can manage this agent.
    try:
        oauth = FairpayOauth2.objects.filter(agent=agent_id)
    except FairpayOauth2.DoesNotExist:
        #TODO: message to user.
        return redirect('fairpay_auth', agent_id=agent_id)
    c = FairpayOauth2Connection.get()
    #TODO: several oauth for one agent.
    try:
        data = c.wallet_history(oauth[0].access_token, limit=10, offset=0)
    except FairpayOauth2Error: # TODO: catch other errors.
        return redirect('fairpay_auth', agent_id=agent_id)

    if data['status'] == 'ok' and data['data']['total'] > 0:
        table_headers = ['created', 'amount', 'currency', 'concept',
                'method_in', 'method_out']
        table_rows = []
        for i in range(data['data']['start'], data['data']['end']):
            table_rows.append([
                data['data']['elements'][i]['created'],
                data['data']['elements'][i]['amount'],
                data['data']['elements'][i]['currency'],
                data['data']['elements'][i]['data_in']['concept'],
                data['data']['elements'][i]['method_in'],
                data['data']['elements'][i]['method_out'],
            ])
        return render(request, 'fairpay_history.html', {
            'table_headers': table_headers,
            'table_rows': table_rows,
            'fairpay_user': oauth[0].fairpay_user,
        })
    else:
        return redirect('fairpay_auth', agent_id=agent_id)
