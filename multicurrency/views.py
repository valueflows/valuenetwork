from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.contrib import messages
from django.utils.dateparse import parse_datetime

from valuenetwork.valueaccounting.models import EconomicAgent
from multicurrency.models import MulticurrencyAuth
from multicurrency.forms import MulticurrencyAuthForm, MulticurrencyAuthDeleteForm
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
        return render(request, 'multicurrency_auth.html', {
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
        data = connection.wallet_history(
            oauth.access_key,
            oauth.access_secret,
            limit=limit,
            offset=offset,
        )
    except ChipChapAuthError:
        messages.error(request,
            'Something was wrong connecting to chip-chap.')
        return redirect('multicurrency_auth', agent_id=agent_id)

    if data['status'] == 'ok':
        methods = {
            'fac': 'FAIR',
            'halcash_es': 'Halcash ES',
        }
        table_caption = "Showing " + str(data['data']['start'] + 1) + " to "\
            + str(data['data']['end']) + " of " + str(data['data']['total'])\
            + " movements"
        table_headers = ['Created', 'Concept', 'Method in',
            'Method out', 'Address', 'Amount']
        table_rows = []
        paginator = {}
        if data['data']['total'] > 0:
            for i in range(data['data']['start'], data['data']['end']):
                tx = data['data']['elements'][i]
                created = parse_datetime(tx['created']) if 'created' in tx else '--'
                concept = tx['concept'] if 'concept' in tx else '--'
                method_in = tx['method_in'] if 'method_in' in tx else '--'
                method_out = tx['method_out'] if 'method_out' in tx else '--'
                address = '--'
                if 'data_in' in tx:
                    address = tx['data_in']['address'] if 'address' in tx['data_in'] else '--'
                if 'data_out' in tx and address == '--':
                    address = tx['data_out']['address'] if 'address' in tx['data_out'] else '--'
                amount = Decimal(tx['amount']) if 'amount' in tx else Decimal('0')
                currency = tx['currency'] if 'currency' in tx else '--'
                if method_in in methods: method_in = methods[method_in]
                if method_out in methods: method_out = methods[method_out]
                if currency == "FAC":
                    currency = "FAIR"
                    amount = amount/1000000
                table_rows.append([
                    created.strftime('%d/%m/%y %H:%M'),
                    concept,
                    method_in,
                    method_out,
                    address,
                    str(amount.quantize(Decimal('0.01'))) + ' ' + currency,
                ])
                if data['data']['total'] > data['data']['end']:
                    paginator['next'] = {
                        'limit': str(items_per_page),
                        'offset': str(data['data']['end'])
                    }
                if data['data']['start'] > items_per_page:
                    paginator['previous'] = {
                        'limit': str(items_per_page),
                        'offset': str(int(data['data']['start']) - items_per_page)
                    }
        return render(request, 'multicurrency_history.html', {
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
