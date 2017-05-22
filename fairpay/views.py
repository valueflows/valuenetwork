from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.contrib import messages

from valuenetwork.valueaccounting.models import EconomicAgent
from fairpay.models import FairpayOauth2
from fairpay.forms import FairpayOauth2Form
from fairpay.utils import FairpayOauth2Connection, FairpayOauth2Error

def get_agents(request, agent_id):

    user_agent = None
    try:
        au = request.user.agent
        user_agent = au.agent
    except:
        pass
    if user_agent and user_agent.id == int(agent_id):
        return True, user_agent, user_agent

    agent = None
    try:
        agent = EconomicAgent.objects.get(id=agent_id)
    except:
        pass
    if user_agent and agent and agent in user_agent.managed_projects():
        return True, user_agent, agent

    return False, user_agent, agent


@login_required
def auth(request, agent_id):
    access_permission, user_agent, agent = get_agents(request, agent_id)
    if not access_permission:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = FairpayOauth2Form(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            connection = FairpayOauth2Connection.get()

            try:
                response = connection.fake_new_token(name, password)
            except FairpayOauth2Error:
                messages.error(request, 'Authentication failed.')
                return redirect('fairpay_auth', agent_id=agent_id)

            try:
                FairpayOauth2.objects.create(
                    agent = agent,
                    fairpay_user = name,
                    access_token = response['access_token'],
                    refresh_token = response['refresh_token'],
                    expires_token = int(response['expires_in']),
                )
            except:
                messages.error(request,
                    'Something was wrong saving your fairpay data.')

            messages.success(request,
                'Your new access to fairpay has been succesfully created.')
            return redirect('fairpay_auth', agent_id=agent_id)
        else:
            messages.error(request, 'Authentication failed.')
            return redirect('fairpay_auth', agent_id=agent_id)
    else:
        try:
            oauths = FairpayOauth2.objects.filter(agent=agent)
        except FairpayOauth2.DoesNotExist:
            oauths = None

        form = FairpayOauth2Form()
        return render(request, 'fairpay_auth.html', {
            'agent': agent,
            'user_agent': user_agent,
            'oauths': oauths,
            'oauth_form': form,
            })


@login_required
def history(request, agent_id, oauth_id):
    access_permission, user_agent, agent = get_agents(request, agent_id)
    if not access_permission:
        return HttpResponseForbidden()

    try:
        oauths = FairpayOauth2.objects.filter(agent=agent)
    except FairpayOauth2.DoesNotExist:
        oauths = None

    if oauths:
        oauth = None
        for o in oauths:
            if o.id == int(oauth_id):
                oauth = o

    if not oauths or not oauth:
        return HttpResponseForbidden()

    connection = FairpayOauth2Connection.get()

    try:
        data = connection.fake_wallet_history(
            oauth.access_token,
            limit=10,
            offset=0
        )
    except FairpayOauth2Error:
        messages.error(request,
            'Something was wrong connecting to chip-chap.')
        return redirect('fairpay_auth', agent_id=agent_id)

    if data['status'] == 'ok':
        table_headers = ['created', 'amount', 'currency', 'concept',
                'method_in', 'method_out']
        table_rows = []
        if data['data']['total'] > 0:
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
            'fairpay_user': oauth.fairpay_user,
        })
    else:
        messages.error(request,
            'Something was wrong connecting to chip-chap.')
        return redirect('fairpay_auth', agent_id=agent_id)
