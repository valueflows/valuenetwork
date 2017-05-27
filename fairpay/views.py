from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.contrib import messages
from django.utils.dateparse import parse_datetime

from valuenetwork.valueaccounting.models import EconomicAgent
from fairpay.models import FairpayOauth2
from fairpay.forms import FairpayOauth2Form, FairpayOauth2DeleteForm
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
        raise PermissionDenied

    if request.method == 'POST':
        form = FairpayOauth2Form(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            connection = FairpayOauth2Connection.get()

            try:
                response = connection.new_client(name, password)
            except FairpayOauth2Error:
                messages.error(request, 'Authentication failed.')
                return redirect('fairpay_auth', agent_id=agent_id)

            try:
                FairpayOauth2.objects.create(
                    agent = agent,
                    fairpay_user = name,
                    access_key = response['access_key'],
                    access_secret = response['access_secret'],
                    created_by = request.user,
                )
            except:
                messages.error(request,
                    'Something was wrong saving your data.')

            messages.success(request,
                'Your ChipChap user has been succesfully authenticated.')
            return redirect('fairpay_auth', agent_id=agent_id)

    else:
        try:
            oauths = FairpayOauth2.objects.filter(agent=agent)
        except FairpayOauth2.DoesNotExist:
            oauths = None

        form = FairpayOauth2Form()
        delete_form = FairpayOauth2DeleteForm()
        return render(request, 'fairpay_auth.html', {
            'agent': agent,
            'user_agent': user_agent,
            'oauths': oauths,
            'oauth_form': form,
            'delete_form': delete_form,
            })

@login_required
def deleteauth(request, agent_id, oauth_id):
    access_permission, user_agent, agent = get_agents(request, agent_id)
    if not access_permission:
        raise PermissionDenied

    try:
        oauths = FairpayOauth2.objects.filter(agent=agent)
    except FairpayOauth2.DoesNotExist:
        raise Http404

    oauth = None
    for o in oauths:
        if o.id == int(oauth_id):
            oauth = o

    if not oauth:
        raise Http404

    if request.method == 'POST':
        form = FairpayOauth2DeleteForm(request.POST)
        if form.is_valid():
            oauth.delete()
            messages.success(request,
                'Your ChipChap user has been succesfully logged out.')
    return redirect('fairpay_auth', agent_id=agent_id)


@login_required
def history(request, agent_id, oauth_id):
    access_permission, user_agent, agent = get_agents(request, agent_id)
    if not access_permission:
        raise PermissionDenied

    try:
        oauths = FairpayOauth2.objects.filter(agent=agent)
    except FairpayOauth2.DoesNotExist:
        raise PermissionDenied

    oauth = None
    for o in oauths:
        if o.id == int(oauth_id):
            oauth = o

    if not oauth:
        raise PermissionDenied

    connection = FairpayOauth2Connection.get()

    try:
        data = connection.fake_wallet_history(
            oauth.access_key,
            oauth.access_secret,
            limit=10,
            offset=0
        )
    except FairpayOauth2Error:
        messages.error(request,
            'Something was wrong connecting to chip-chap.')
        return redirect('fairpay_auth', agent_id=agent_id)

    if data['status'] == 'ok':
        methods = {
            'fac': 'FAIR',
            'halcash_es': 'Halcash ES',
        }
        table_caption = ("Showing from " + str(data['data']['start'])\
            + " to " + str(data['data']['end'])\
            + " -- Total movements: " + str(data['data']['total'])\
            + " -- Agent: " + agent.name + " -- ChipChap user: "\
            + oauth.fairpay_user)
        table_headers = ['Created', 'Concept', 'Method in',
            'Method out', 'Amount']
        table_rows = []
        if data['data']['total'] > 0:
            for i in range(data['data']['start'], data['data']['end']):
                created = parse_datetime(data['data']['elements'][i]['created'])
                method_in = data['data']['elements'][i]['method_in']
                method_out = data['data']['elements'][i]['method_out']
                amount = Decimal(data['data']['elements'][i]['amount'])
                currency = data['data']['elements'][i]['currency']
                if method_in in methods:
                    method_in = methods[method_in]
                if method_out in methods:
                    method_out = methods[method_out]
                if currency == "FAC": currency = "FAIR"
                table_rows.append([
                    created.strftime('%d/%m/%y %H:%M'),
                    data['data']['elements'][i]['data_in']['concept'],
                    method_in,
                    method_out,
                    str(amount.quantize(Decimal('0.01'))) + ' ' + currency,
                ])
        return render(request, 'fairpay_history.html', {
            'table_caption': table_caption,
            'table_headers': table_headers,
            'table_rows': table_rows,
            'fairpay_user': oauth.fairpay_user,
        })
    else:
        messages.error(request,
            'Something was wrong connecting to chip-chap.')
        return redirect('fairpay_auth', agent_id=agent_id)
