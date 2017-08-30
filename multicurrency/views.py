from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.contrib import messages
from django.utils.dateparse import parse_datetime

from valuenetwork.valueaccounting.models import EconomicAgent
from multicurrency.models import MulticurrencyAuth
from multicurrency.forms import MulticurrencyAuthForm, MulticurrencyAuthDeleteForm, \
    MulticurrencyAuthCreateForm
from multicurrency.utils import ChipChapAuthConnection, ChipChapAuthError

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
        form = MulticurrencyAuthForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            connection = ChipChapAuthConnection.get()

            try:
                response = connection.new_client(name, password)
            except ChipChapAuthError as e:
                messages.error(request, 'Authentication failed.')
                return redirect('multicurrency_auth', agent_id=agent_id)

            try:
                MulticurrencyAuth.objects.create(
                    agent = agent,
                    auth_user = name,
                    access_key = response['access_key'],
                    access_secret = response['access_secret'],
                    created_by = request.user,
                )
            except:
                messages.error(request,
                    'Something was wrong saving your data.')

            messages.success(request,
                'Your ChipChap user has been succesfully authenticated.')
            return redirect('multicurrency_auth', agent_id=agent_id)

    else:
        try:
            oauths = MulticurrencyAuth.objects.filter(agent=agent)
        except MulticurrencyAuth.DoesNotExist:
            oauths = None

        form = MulticurrencyAuthForm()
        delete_form = MulticurrencyAuthDeleteForm()
        create_form = MulticurrencyAuthCreateForm(initial={
            'username': agent.nick,
            'email': agent.email,
            })
        return render(request, 'multicurrency_auth.html', {
            'agent': agent,
            'user_agent': user_agent,
            'oauths': oauths,
            'oauth_form': form,
            'create_form': create_form,
            'delete_form': delete_form,
            })

@login_required
def deleteauth(request, agent_id, oauth_id):
    access_permission, user_agent, agent = get_agents(request, agent_id)
    if not access_permission:
        raise PermissionDenied

    try:
        oauths = MulticurrencyAuth.objects.filter(agent=agent)
    except MulticurrencyAuth.DoesNotExist:
        raise Http404

    oauth = None
    for o in oauths:
        if o.id == int(oauth_id):
            oauth = o

    if not oauth:
        raise Http404

    if request.method == 'POST':
        form = MulticurrencyAuthDeleteForm(request.POST)
        if form.is_valid():
            oauth.delete()
            messages.success(request,
                'Your ChipChap user has been succesfully logged out.')
    return redirect('multicurrency_auth', agent_id=agent_id)

@login_required
def createauth(request, agent_id):
    access_permission, user_agent, agent = get_agents(request, agent_id)
    if not access_permission:
        raise PermissionDenied

    if request.method == 'POST':
        form = MulticurrencyAuthCreateForm(request.POST)
        if form.is_valid():
            connection = ChipChapAuthConnection.get()
            try:
                response = connection.new_chipchap_user(
                    username=agent.nick,
                    email=agent.email,
                    company_name=agent.nick,
                    password=form.cleaned_data['password'],
                    repassword=form.cleaned_data['password'],
                )
            except ChipChapAuthError:
                messages.error(request, 'Something was wrong creating new chip-chap user.')
                return redirect('multicurrency_auth', agent_id=agent_id)
            # TODO: save new auth with response data (no password yet)
            messages.success(request,
                'Your ChipChap user ' + agent.nick + ' has been succesfully created.'
                + 'Check your email in order of confirming it in ChipChap system.'
                + 'Come back here with your credentials, and authenticate your user.')

    return redirect('multicurrency_auth', agent_id=agent_id)

@login_required
def history(request, agent_id, oauth_id):
    access_permission, user_agent, agent = get_agents(request, agent_id)
    if not access_permission:
        raise PermissionDenied

    try:
        oauths = MulticurrencyAuth.objects.filter(agent=agent)
    except MulticurrencyAuth.DoesNotExist:
        raise PermissionDenied

    oauth = None
    for o in oauths:
        if o.id == int(oauth_id):
            oauth = o

    if not oauth:
        raise PermissionDenied

    items_per_page = 25
    try:
        limit = int(request.GET.get('limit', str(items_per_page)))
        offset = int(request.GET.get('offset', '0'))
    except:
        limit = items_per_page
        offset = 0

    connection = ChipChapAuthConnection.get()
    try:
        tx_list, balance = connection.wallet_history(
            oauth.access_key,
            oauth.access_secret,
            limit=limit,
            offset=offset,
        )
    except ChipChapAuthError:
        messages.error(request,
            'Something was wrong connecting to chip-chap.')
        return redirect('multicurrency_auth', agent_id=agent_id)

    if tx_list['status'] == 'ok' and balance['status'] == 'ok':
        balance_clean = []
        for bal in balance['data']:
            if int(bal['balance']) != 0:
                clean_bal = Decimal(int(bal['balance']))/(10**int(bal['scale']))
                clean_currency = bal['currency'] if bal['currency'] != 'FAC' else 'FAIR'
                balance_clean.append(str(clean_bal.quantize(Decimal('0.01'))) + ' ' + clean_currency)
        methods = {
            'fac': 'FAIR',
            'halcash_es': 'Halcash ES',
            'exchange_EURtoFAC': 'EUR to FAIR',
            'sepa': 'SEPA',
            'wallet_to_wallet': 'wallet to wallet',
        }
        table_caption = "Showing " + str(tx_list['data']['start'] + 1) + " to "\
            + str(tx_list['data']['end']) + " of " + str(tx_list['data']['total'])\
            + " movements"
        table_headers = ['Created', 'Concept', 'Method', 'Address', 'Amount']
        table_rows = []
        paginator = {}
        if tx_list['data']['total'] > 0:
            for tx in tx_list['data']['elements']:
                created = parse_datetime(tx['created']) if 'created' in tx else '--'
                concept = '--'
                address = '--'
                if 'pay_in_info' in tx:
                    concept = tx['pay_in_info']['concept'] if 'concept' in tx['pay_in_info'] else '--'
                    address = tx['pay_in_info']['address'] if 'address' in tx['pay_in_info'] else '--'
                elif 'pay_out_info' in tx:
                    concept = tx['pay_out_info']['concept'] if 'concept' in tx['pay_out_info'] else '--'
                    address = tx['pay_out_info']['address'] if 'address' in tx['pay_out_info'] else '--'
                method = tx['method'] if 'method' in tx else '--'
                if method in methods: method = methods[method]
                amount = Decimal(tx['amount']) if 'amount' in tx else Decimal('0')
                scale = int(tx['scale']) if 'scale' in tx else 0
                amount = amount/(10**scale)
                if 'type' in tx:
                    amount = -amount if tx['type'] == 'out' else amount
                currency = tx['currency'] if 'currency' in tx else '--'
                if currency == "FAC": currency = "FAIR"
                table_rows.append([
                    created.strftime('%d/%m/%y %H:%M'),
                    concept,
                    method,
                    address,
                    str(amount.quantize(Decimal('0.01'))) + ' ' + currency,
                ])
                if tx_list['data']['total'] > tx_list['data']['end']:
                    paginator['next'] = {
                        'limit': str(items_per_page),
                        'offset': str(tx_list['data']['end'])
                    }
                if tx_list['data']['start'] >= items_per_page:
                    paginator['previous'] = {
                        'limit': str(items_per_page),
                        'offset': str(int(tx_list['data']['start']) - items_per_page)
                    }
        return render(request, 'multicurrency_history.html', {
            'balance_clean': balance_clean,
            'table_caption': table_caption,
            'table_headers': table_headers,
            'table_rows': table_rows,
            'auth_user': oauth.auth_user,
            'oauth_id': oauth.id,
            'agent': agent,
            'offset': offset,
            'paginator': paginator,
        })
    else:
        messages.error(request,
            'Something was wrong connecting to chip-chap.')
        return redirect('multicurrency_auth', agent_id=agent_id)
