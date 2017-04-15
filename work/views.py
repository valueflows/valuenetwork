#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from django.db.models import Q
from django.http import HttpResponse, HttpResponseServerError, Http404, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.template import RequestContext
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.forms.models import formset_factory, modelformset_factory, inlineformset_factory, BaseModelFormSet
from django.forms import ValidationError
import json as simplejson
from collections import OrderedDict
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import validators
from django.utils.translation import ugettext, ugettext_lazy as _

from valuenetwork.valueaccounting.models import *
from valuenetwork.valueaccounting.forms import *
from valuenetwork.valueaccounting.service import ExchangeService
from work.forms import *
from valuenetwork.valueaccounting.views import *
#from valuenetwork.valueaccounting.views import get_agent, get_help, get_site_name, resource_role_agent_formset, uncommit, commitment_finished, commit_to_task
import valuenetwork.valueaccounting.faircoin_utils as faircoin_utils
from valuenetwork.valueaccounting.service import ExchangeService

from fobi.models import FormEntry
from general.models import Artwork_Type, Unit_Type

if "pinax.notifications" in settings.INSTALLED_APPS:
    from pinax.notifications import models as notification
else:
    notification = None

def get_site_name():
    return Site.objects.get_current().name

def get_url_starter():
    return "".join(["https://", Site.objects.get_current().domain])

def work_home(request):

    return render(request, "work_home.html", {
        "help": get_help("work_home"),
    })


@login_required
def my_dashboard(request):
    #import pdb; pdb.set_trace()
    agent = get_agent(request)

    return render(request, "work/my_dashboard.html", {
        "agent": agent,
    })


def new_features(request):
    new_features = NewFeature.objects.all()

    return render(request, "work/new_features.html", {
        "new_features": new_features,
        "photo_size": (256, 256),
    })

def map(request):
    agent = get_agent(request)
    locations = Location.objects.all()
    nolocs = Location.objects.filter(latitude=0.0)
    latitude = settings.MAP_LATITUDE
    longitude = settings.MAP_LONGITUDE
    zoom = settings.MAP_ZOOM
    return render(request, "work/map.html", {
        "agent": agent,
        "locations": locations,
        "nolocs": nolocs,
        "latitude": latitude,
        "longitude": longitude,
        "zoom": zoom,
        "help": get_help("work_map"),
    })



#    P R O F I L E

@login_required
def profile(request):
    #import pdb; pdb.set_trace()
    agent = get_agent(request)
    change_form = WorkAgentCreateForm(instance=agent)
    skills = EconomicResourceType.objects.filter(behavior="work")
    et_work = EventType.objects.get(name="Time Contribution")
    arts = agent.resource_types.filter(event_type=et_work)
    agent_skills = []
    user = request.user
    suggestions = user.skill_suggestion.all()
    suggested_skills = [sug.resource_type for sug in suggestions]
    for art in arts:
        agent_skills.append(art.resource_type)
    for skill in skills:
        skill.checked = False
        if skill in agent_skills:
            skill.checked = True
        if skill in suggested_skills:
            skill.thanks = True
    upload_form = UploadAgentForm(instance=agent)
    has_associations = agent.all_has_associates()
    is_associated_with = agent.all_is_associates()
    other_form = SkillSuggestionForm()
    suggestions = request.user.skill_suggestion.all()
    faircoin_account = agent.faircoin_resource()
    balance = 0
    if faircoin_account:
        balance = faircoin_account.digital_currency_balance()

    other_form = SkillSuggestionForm()
    suggestions = request.user.skill_suggestion.all()
    #balance = 2
    candidate_membership = agent.candidate_membership()

    return render(request, "work/profile.html", {
        "agent": agent,
        "photo_size": (128, 128),
        "change_form": change_form,
        "upload_form": upload_form,
        "skills": skills,
        "has_associations": has_associations,
        "is_associated_with": is_associated_with,
        "faircoin_account": faircoin_account,
        "balance": balance,
        #"payment_due": payment_due,
        "candidate_membership": candidate_membership,
        "other_form": other_form,
        "suggestions": suggestions,
        "help": get_help("profile"),
        #"share_price": share_price,
        #"number_of_shares": number_of_shares,
        #"can_pay": can_pay,
    })


@login_required
def change_personal_info(request, agent_id):
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    user_agent = get_agent(request)
    if not user_agent:
        return render(request, 'work/no_permission.html')
    change_form = WorkAgentCreateForm(instance=agent, data=request.POST or None)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        if change_form.is_valid():
            agent = change_form.save()
    return HttpResponseRedirect('/%s/'
        % ('work/profile'))

@login_required
def upload_picture(request, agent_id):
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    user_agent = get_agent(request)
    if not user_agent:
        return render(request, 'valueaccounting/no_permission.html')
    form = UploadAgentForm(instance=agent, data=request.POST, files=request.FILES)
    if form.is_valid():
        data = form.cleaned_data
        agt = form.save(commit=False)
        agt.changed_by=request.user
        agt.save()

    return HttpResponseRedirect('/%s/'
        % ('work/profile'))

@login_required
def add_worker_to_location(request, location_id, agent_id):
    if location_id and agent_id:
        location = get_object_or_404(Location, id=location_id)
        agent = get_object_or_404(EconomicAgent, id=agent_id)
        agent.primary_location = location
        agent.save()
        return HttpResponseRedirect('/%s/'
            % ('work/profile'))
    else:
        return HttpResponseRedirect('/%s/'
            % ('work/map'))

@login_required
def add_location_to_worker(request, agent_id):
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        agent = get_object_or_404(EconomicAgent, id=agent_id)
        data = request.POST
        address = data["address"]
        longitude = data["agentLongitude"]
        latitude = data["agentLatitude"]
        location, created = Location.objects.get_or_create(
            latitude=latitude,
            longitude=longitude,
            address=address)
        if created:
            location.name = address
            location.save()
        agent.primary_location = location
        agent.save()
        return HttpResponseRedirect('/%s/'
            % ('work/profile'))
    else:
        return HttpResponseRedirect('/%s/'
            % ('work/map'))


#   P R O F I L E   S K I L L S

@login_required
def update_skills(request, agent_id):
    if request.method == "POST":
        agent = get_object_or_404(EconomicAgent, id=agent_id)
        user_agent = get_agent(request)
        if not user_agent:
            return render(request, 'valueaccounting/no_permission.html')
        #import pdb; pdb.set_trace()
        et_work = EventType.objects.get(name="Time Contribution")
        arts = agent.resource_types.filter(event_type=et_work)
        old_skill_rts = []
        for art in arts:
            old_skill_rts.append(art.resource_type)
        new_skills_list = request.POST.getlist('skillChoice')
        new_skill_rts = []
        for rt_id in new_skills_list:
            skill = EconomicResourceType.objects.get(id=int(rt_id))
            new_skill_rts.append(skill)
        for skill in old_skill_rts:
            if skill not in new_skill_rts:
                arts = AgentResourceType.objects.filter(agent=agent).filter(resource_type=skill)
                if arts:
                    art = arts[0]
                    art.delete()
        for skill in new_skill_rts:
            if skill not in old_skill_rts:
                art = AgentResourceType(
                    agent=agent,
                    resource_type=skill,
                    event_type=et_work,
                    created_by=request.user,
                )
                art.save()
        other_form = SkillSuggestionForm(data=request.POST)
        #import pdb; pdb.set_trace()
        if other_form.is_valid():
            suggestion = other_form.save(commit=False)
            suggestion.suggested_by = request.user
            suggestion.save()
            try:
                suggester = request.user.agent.agent
            except:
                suggester = request.user
            if notification:
                users = User.objects.filter(is_staff=True)
                suggestions_url = get_url_starter() + "/accounting/skill-suggestions/"
                if users:
                    site_name = get_site_name()
                    notification.send(
                        users,
                        "work_skill_suggestion",
                        {"skill": suggestion.skill,
                        "suggested_by": suggester.name,
                        "suggestions_url": suggestions_url,
                        }
                    )

    return HttpResponseRedirect('/%s/'
        % ('work/profile'))


'''
@login_required
def register_skills(request):
    #import pdb; pdb.set_trace()
    agent = get_agent(request)
    skills = EconomicResourceType.objects.filter(behavior="work")

    return render(request, "work/register_skills.html", {
        "agent": agent,
        "skills": skills,
    })
'''


#    F A I R C O I N

@login_required
def manage_faircoin_account(request, resource_id):
    #import pdb; pdb.set_trace()
    resource = get_object_or_404(EconomicResource, id=resource_id)
    agent = get_agent(request)
    send_coins_form = None
    limit = 0

    payment_due = False
    candidate_membership = None
    share_price = False
    number_of_shares = False
    can_pay = False
    faircoin_account = False
    balance = False

    if agent:
        if agent.owns(resource) or resource.owner() in agent.managed_projects():
            send_coins_form = SendFairCoinsForm(agent=resource.owner())
            #from valuenetwork.valueaccounting.faircoin_utils import network_fee
            limit = resource.spending_limit()

        candidate_membership = agent.candidate_membership()
        if candidate_membership:
            faircoin_account = agent.faircoin_resource()
            balance = 0
            if faircoin_account:
                balance = faircoin_account.digital_currency_balance_unconfirmed()
            share = EconomicResourceType.objects.membership_share()
            share_price = share.price_per_unit
            number_of_shares = agent.number_of_shares()
            share_price = share_price * number_of_shares
            payment_due = False
            if not agent.owns_resource_of_type(share):
                payment_due = True
            can_pay = balance >= share_price

    return render(request, "work/faircoin_account.html", {
        "resource": resource,
        "photo_size": (128, 128),
        "agent": agent,
        "send_coins_form": send_coins_form,
        "limit": limit,

        "payment_due": payment_due,
        "candidate_membership": candidate_membership,
        "help": get_help("profile"),
        "share_price": share_price,
        "number_of_shares": number_of_shares,
        "can_pay": can_pay,
        "faircoin_account": faircoin_account,
        "balance": balance,

    })

def validate_faircoin_address_for_worker(request):
    #import pdb; pdb.set_trace()
    from valuenetwork.valueaccounting.faircoin_utils import is_valid
    data = request.GET
    address = data["to_address"].strip()
    answer = is_valid(address)
    if not answer:
        answer = "Invalid FairCoin address"
    response = simplejson.dumps(answer, ensure_ascii=False)
    return HttpResponse(response, content_type="text/json-comment-filtered")

@login_required
def change_faircoin_account(request, resource_id):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        resource = get_object_or_404(EconomicResource, pk=resource_id)
        form = EconomicResourceForm(data=request.POST, instance=resource)
        if form.is_valid():
            data = form.cleaned_data
            resource = form.save(commit=False)
            resource.changed_by=request.user
            resource.save()
            """
            RraFormSet = modelformset_factory(
                AgentResourceRole,
                form=ResourceRoleAgentForm,
                can_delete=True,
                extra=4,
                )
            role_formset = RraFormSet(
                prefix="role",
                queryset=resource.agent_resource_roles.all(),
                data=request.POST
                )
            if role_formset.is_valid():
                saved_formset = role_formset.save(commit=False)
                for role in saved_formset:
                    role.resource = resource
                    role.save()
            """
            return HttpResponseRedirect('/%s/%s/'
                % ('work/manage-faircoin-account', resource_id))
        else:
            raise ValidationError(form.errors)

@login_required
def transfer_faircoins(request, resource_id):
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        resource = get_object_or_404(EconomicResource, id=resource_id)
        agent = get_agent(request)
        to_agent = request.POST["to_user"]
        send_coins_form = SendFairCoinsForm(data=request.POST, agent=resource.owner())
        if send_coins_form.is_valid():
            data = send_coins_form.cleaned_data
            address_end = data["to_address"]
            quantity = data["quantity"]
            notes = data["description"]
            address_origin = resource.digital_currency_address
            if address_origin and address_end:
                from_agent = resource.owner()
                to_resources = EconomicResource.objects.filter(digital_currency_address=address_end)
                to_agent = None
                if to_resources:
                    to_resource = to_resources[0] #shd be only one
                    to_agent = to_resource.owner()
                et_give = EventType.objects.get(name="Give")
                if to_agent:
                    tt = ExchangeService.faircoin_internal_transfer_type()
                    xt = tt.exchange_type
                    date = datetime.date.today()
                    exchange = Exchange(
                        exchange_type=xt,
                        use_case=xt.use_case,
                        name="Transfer Faircoins",
                        start_date=date,
                        notes=notes,
                        #context_agent=from_agent, # don't set it to allow to_agent to see the exchange
                    )
                    exchange.save()
                    transfer = Transfer(
                        transfer_type=tt,
                        exchange=exchange,
                        transfer_date=date,
                        name="Transfer Faircoins",
                        notes=notes,
                        context_agent=from_agent,
                    )
                    transfer.save()
                else:
                    tt = ExchangeService.faircoin_outgoing_transfer_type()
                    xt = tt.exchange_type
                    date = datetime.date.today()
                    exchange = Exchange(
                        exchange_type=xt,
                        use_case=xt.use_case,
                        name="Send Faircoins",
                        start_date=date,
                        notes=notes,
                        context_agent=from_agent,
                    )
                    exchange.save()
                    transfer = Transfer(
                        transfer_type=tt,
                        exchange=exchange,
                        transfer_date=date,
                        name="Send Faircoins",
                        notes=notes,
                        context_agent=from_agent,
                    )
                    transfer.save()

                # network_fee is subtracted from quantity
                # so quantity is correct for the giving event
                # but receiving event will get quantity - network_fee
                state =  "new"
                event = EconomicEvent(
                    event_type = et_give,
                    event_date = date,
                    from_agent=from_agent,
                    to_agent=to_agent,
                    resource_type=resource.resource_type,
                    resource=resource,
                    digital_currency_tx_state = state,
                    quantity = quantity,
                    transfer=transfer,
                    event_reference=address_end,
                    description=notes,
                    )
                event.save()
                if to_agent:
                    from valuenetwork.valueaccounting.faircoin_utils import network_fee
                    quantity = quantity - Decimal(float(network_fee()) / 1.e6)
                    et_receive = EventType.objects.get(name="Receive")
                    event = EconomicEvent(
                        event_type = et_receive,
                        event_date = date,
                        from_agent=from_agent,
                        to_agent=to_agent,
                        resource_type=to_resource.resource_type,
                        resource=to_resource,
                        digital_currency_tx_state = state,
                        quantity = quantity,
                        transfer=transfer,
                        event_reference=address_end,
                        description=notes,
                        )
                    event.save()
                    #print "receive event:", event

                return HttpResponseRedirect('/%s/%s/'
                    % ('work/faircoin-history', resource.id))

        return HttpResponseRedirect('/%s/%s/'
                % ('work/manage-faircoin-account', resource.id))

"""
@login_required
def transfer_faircoins_old(request, resource_id):
    if request.method == "POST":
        resource = get_object_or_404(EconomicResource, id=resource_id)
        agent = get_agent(request)
        send_coins_form = SendFairCoinsForm(data=request.POST)
        if send_coins_form.is_valid():
            data = send_coins_form.cleaned_data
            address_end = data["to_address"]
            quantity = data["quantity"]
            address_origin = resource.digital_currency_address
            if address_origin and address_end:
                from valuenetwork.valueaccounting.faircoin_utils import send_faircoins, get_confirmations, network_fee
                tx, broadcasted = send_faircoins(address_origin, address_end, quantity)
                if tx:
                    tx_hash = tx.hash()
                    from_agent = resource.owner()
                    to_resources = EconomicResource.objects.filter(digital_currency_address=address_end)
                    to_agent = None
                    if to_resources:
                        to_resource = to_resources[0] #shd be only one
                        to_agent = to_resource.owner()
                    et_give = EventType.objects.get(name="Give")
                    if to_agent:
                        tt = ExchangeService.faircoin_internal_transfer_type()
                        xt = tt.exchange_type
                        date = datetime.date.today()
                        exchange = Exchange(
                            exchange_type=xt,
                            use_case=xt.use_case,
                            name="Transfer Faircoins",
                            start_date=date,
                            )
                        exchange.save()
                        transfer = Transfer(
                            transfer_type=tt,
                            exchange=exchange,
                            transfer_date=date,
                            name="Transfer Faircoins",
                            )
                        transfer.save()
                    else:
                        tt = ExchangeService.faircoin_outgoing_transfer_type()
                        xt = tt.exchange_type
                        date = datetime.date.today()
                        exchange = Exchange(
                            exchange_type=xt,
                            use_case=xt.use_case,
                            name="Send Faircoins",
                            start_date=date,
                            )
                        exchange.save()
                        transfer = Transfer(
                            transfer_type=tt,
                            exchange=exchange,
                            transfer_date=date,
                            name="Send Faircoins",
                            )
                        transfer.save()

                    # network_fee is subtracted from quantity
                    # so quantity is correct for the giving event
                    # but receiving event will get quantity - network_fee
                    state = "pending"
                    if not broadcasted:
                        confirmations = get_confirmations(tx_hash)
                        if confirmations[0]:
                            print "got broadcasted in view"
                            broadcasted = True
                    if broadcasted:
                        state = "broadcast"
                    event = EconomicEvent(
                        event_type = et_give,
                        event_date = date,
                        from_agent=from_agent,
                        to_agent=to_agent,
                        resource_type=resource.resource_type,
                        resource=resource,
                        digital_currency_tx_hash = tx_hash,
                        digital_currency_tx_state = state,
                        quantity = quantity,
                        transfer=transfer,
                        event_reference=address_end,
                        )
                    event.save()
                    if to_agent:
                        outputs = tx.get_outputs()
                        value = 0
                        for address, val in outputs:
                            if address == address_end:
                                value = val
                        if value:
                            quantity = Decimal(value / 1.e6)
                        else:
                            quantity = quantity - Decimal(float(network_fee) / 1.e6)
                        et_receive = EventType.objects.get(name="Receive")
                        event = EconomicEvent(
                            event_type = et_receive,
                            event_date = date,
                            from_agent=from_agent,
                            to_agent=to_agent,
                            resource_type=to_resource.resource_type,
                            resource=to_resource,
                            digital_currency_tx_hash = tx_hash,
                            digital_currency_tx_state = state,
                            quantity = quantity,
                            transfer=transfer,
                            )
                        event.save()
                        print "receive event:", event

                    return HttpResponseRedirect('/%s/%s/'
                        % ('work/faircoin-history', resource.id))

            return HttpResponseRedirect('/%s/%s/'
                    % ('work/manage-faircoin-account', resource.id))
"""

@login_required
def faircoin_history(request, resource_id):
    resource = get_object_or_404(EconomicResource, id=resource_id)
    agent = get_agent(request)
    exchange_service = ExchangeService.get()
    exchange_service.include_blockchain_tx_as_event(resource.owner(), resource)
    event_list = resource.events.all()
    init = {"quantity": resource.quantity,}
    unit = resource.resource_type.unit

    paginator = Paginator(event_list, 25)

    page = request.GET.get('page')
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        events = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        events = paginator.page(paginator.num_pages)
    if resource.owner() == agent or resource.owner() in agent.managed_projects() or agent.is_staff():
        return render(request, "work/faircoin_history.html", {
            "resource": resource,
            "agent": agent,
            "unit": unit,
            "events": events,
        })
    else:
        return render(request, 'work/no_permission.html')



@login_required
def edit_faircoin_event_description(request, resource_id):
    agent = get_agent(request)
    resource = EconomicResource.objects.get(id=resource_id)
    if request.method == "POST":
        data = request.POST
        evid = data['id']
        ntext = data['value']
        event = EconomicEvent.objects.get(id=evid)
        event.description = ntext
        event.save()
        return HttpResponse("Ok", content_type="text/plain")
    return HttpResponse("Fail", content_type="text/plain")






#    M E M B E R S H I P



@login_required
def share_payment(request, agent_id):
    #import pdb; pdb.set_trace()
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    agent_account = agent.faircoin_resource()
    balance = agent_account.digital_currency_balance()
    #balance = 2
    candidate_membership = agent.candidate_membership()
    share = EconomicResourceType.objects.membership_share()
    share_price = share.price_per_unit
    number_of_shares = agent.number_of_shares()
    share_price = share_price * number_of_shares

    if share_price <= balance:
        pay_to_id = settings.SEND_MEMBERSHIP_PAYMENT_TO
        pay_to_agent = EconomicAgent.objects.get(nick=pay_to_id)
        pay_to_account = pay_to_agent.faircoin_resource()
        quantity = Decimal(share_price)
        address_origin = agent_account.digital_currency_address
        address_end = pay_to_account.digital_currency_address
        xt = ExchangeType.objects.membership_share_exchange_type()
        tts = xt.transfer_types.all()
        tt_share = tts.get(name__contains="Share")
        tt_fee = tts.get(name__contains="Fee")
        from_agent = agent
        to_resource = pay_to_account
        to_agent = pay_to_agent
        et_give = EventType.objects.get(name="Give")
        et_receive = EventType.objects.get(name="Receive")
        date = datetime.date.today()
        fc = EconomicAgent.objects.freedom_coop()

        exchange = Exchange(
            exchange_type=xt,
            use_case=xt.use_case,
            name="Transfer Faircoins",
            start_date=date,
            )
        exchange.save()

        transfer_fee = Transfer(
            transfer_type=tt_fee,
            exchange=exchange,
            transfer_date=date,
            name="Transfer Faircoins",
            )
        transfer_fee.save()

        transfer_membership = Transfer(
            transfer_type=tt_share,
            exchange=exchange,
            transfer_date=date,
            name="Transfer Membership",
            )
        transfer_membership.save()

        # network_fee is subtracted from quantity
        # so quantity is correct for the giving event
        # but receiving event will get quantity - network_fee
        state =  "new"
        resource = agent_account
        event = EconomicEvent(
            event_type = et_give,
            event_date = date,
            from_agent=from_agent,
            to_agent=to_agent,
            resource_type=resource.resource_type,
            resource=resource,
            digital_currency_tx_state = state,
            quantity = quantity,
            transfer=transfer_fee,
            event_reference=address_end,
            )
        event.save()

        from valuenetwork.valueaccounting.faircoin_utils import network_fee
        quantity = quantity - Decimal(float(network_fee()) / 1.e6)

        event = EconomicEvent(
            event_type = et_receive,
            event_date = date,
            from_agent=from_agent,
            to_agent=to_agent,
            resource_type=to_resource.resource_type,
            resource=to_resource,
            digital_currency_tx_state = state,
            quantity = quantity,
            transfer=transfer_fee,
            event_reference=address_end,
            )
        event.save()

        #import pdb; pdb.set_trace()
        quantity = Decimal(number_of_shares)
        resource = EconomicResource(
            resource_type=share,
            quantity=quantity,
            identifier=" ".join([from_agent.name, share.name]),
            )
        resource.save()

        owner_role = AgentResourceRoleType.objects.owner_role()

        arr = AgentResourceRole(
            agent=from_agent,
            resource=resource,
            role=owner_role,
            is_contact=True,
            )
        arr.save()

        event = EconomicEvent(
            event_type = et_give,
            event_date = date,
            from_agent=to_agent,
            to_agent=from_agent,
            resource_type=resource.resource_type,
            resource=resource,
            quantity = quantity,
            transfer=transfer_membership,
            )
        event.save()

        event = EconomicEvent(
            event_type = et_receive,
            event_date = date,
            from_agent=to_agent,
            to_agent=from_agent,
            resource_type=resource.resource_type,
            resource=resource,
            quantity = quantity,
            transfer=transfer_membership,
            )
        event.save()

        #import pdb; pdb.set_trace()
        aa = agent.candidate_association()

        if aa:
            if aa.has_associate == pay_to_agent:
                aa.delete()

        association_type = AgentAssociationType.objects.get(name="Member")
        fc_aa = AgentAssociation(
            is_associate=agent,
            has_associate=fc,
            association_type=association_type,
            state="active",
            )
        fc_aa.save()

    return HttpResponseRedirect('/%s/'
        % ('work/home'))


def membership_request(request):
    membership_form = MembershipRequestForm(data=request.POST or None)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        if membership_form.is_valid():
            human = True
            data = membership_form.cleaned_data
            type_of_membership = data["type_of_membership"]
            number_of_shares = data["number_of_shares"]
            name = data["name"]
            surname = data["surname"]
            description = data["description"]
            mbr_req = membership_form.save()

            event_type = EventType.objects.get(relationship="todo")
            description = "Create an Agent and User for the Membership Request from "
            description += name
            membership_url= get_url_starter() + "/accounting/membership-request/" + str(mbr_req.id) + "/"
            context_agent=EconomicAgent.objects.get(name__icontains="Membership Request")
            resource_types = EconomicResourceType.objects.filter(behavior="work")
            rts = resource_types.filter(
                Q(name__icontains="Admin")|
                Q(name__icontains="Coop")|
                Q(name__icontains="Work"))
            if rts:
                rt = rts[0]
            else:
                rt = resource_types[0]

            task = Commitment(
                event_type=event_type,
                description=description,
                resource_type=rt,
                context_agent=context_agent,
                url=membership_url,
                due_date=datetime.date.today(),
                quantity=Decimal("1")
                )
            task.save()


            if notification:
                users = User.objects.filter(is_staff=True)
                if users:
                    site_name = get_site_name()
                    notification.send(
                        users,
                        "work_membership_request",
                        {"name": name,
                        "surname": surname,
                        "type_of_membership": type_of_membership,
                        "description": description,
                        "site_name": site_name,
                        "membership_url": membership_url,
                        }
                    )

            return HttpResponseRedirect('/%s/'
                % ('membershipthanks'))
    return render(request, "work/membership_request.html", {
        "help": get_help("work_membership_request"),
        "membership_form": membership_form,
    })


def membership_discussion(request, membership_request_id):
    user_agent = get_agent(request)
    mbr_req = get_object_or_404(MembershipRequest, pk=membership_request_id)
    allowed = False
    if user_agent:
        if user_agent.membership_request() == mbr_req or request.user.is_staff:
            allowed = True
    if not allowed:
        return render(request, 'work/no_permission.html')

    return render(request, "work/membership_request_with_comments.html", {
        "help": get_help("membership_request"),
        "mbr_req": mbr_req,
        "user_agent": user_agent,
    })




#    P R O J E C T S

@login_required
def your_projects(request):
    #import pdb; pdb.set_trace()
    agent = get_agent(request)
    agent_form = ProjectCreateForm() #initial={'agent_type': 'Project'})
    projects = agent.related_contexts()
    managed_projects = agent.managed_projects()
    join_projects = Project.objects.all() #filter(joining_style="moderated", visibility!="private")

    next = "/work/your-projects/"
    allowed = False
    if agent:
        if agent.is_active_freedom_coop_member() or request.user.is_staff or agent.is_participant() or managed_projects:
            allowed = True
    if not allowed:
        return render(request, 'work/no_permission.html')

    for node in projects:
        aats = []
        for aat in node.agent_association_types():
          #if aat.association_behavior != "child":
          aat.assoc_count = node.associate_count_of_type(aat.identifier)
          assoc_list = node.all_has_associates_by_type(aat.identifier)
          for assoc in assoc_list:
            association = AgentAssociation.objects.get(is_associate=assoc, has_associate=node, association_type=aat)#
            assoc.state = association.state
          aat.assoc_list = assoc_list
          if not aat in aats:
            aats.append(aat)
        node.aats = aats

    '''roots = [p for p in projects if not p.is_root()] # if p.is_root()

    for root in roots:
        root.nodes = root.child_tree()
        annotate_tree_properties(root.nodes)
        #import pdb; pdb.set_trace()
        for node in root.nodes:
            aats = []
            for aat in node.agent_association_types():
                #if aat.association_behavior != "child":
                    aat.assoc_count = node.associate_count_of_type(aat.identifier)
                    assoc_list = node.all_has_associates_by_type(aat.identifier)
                    for assoc in assoc_list:
                        association = AgentAssociation.objects.get(is_associate=assoc, has_associate=node, association_type=aat)#
                        assoc.state = association.state
                    aat.assoc_list = assoc_list
                    if not aat in aats:
                      aats.append(aat)
            node.aats = aats'''

    return render(request, "work/your_projects.html", {
        "projects": projects,
        "help": get_help("your_projects"),
        "agent": agent,
        "agent_form": agent_form,
        "managed_projects": managed_projects,
        "join_projects": join_projects,
    })


@login_required
def create_your_project(request):
    user_agent = get_agent(request)
    if not user_agent or not user_agent.is_active_freedom_coop_member:
        return render(request, 'work/no_permission.html')
    if request.method == "POST":
        pro_form = ProjectCreateForm(request.POST)
        agn_form = AgentCreateForm(request.POST)
        if pro_form.is_valid() and agn_form.is_valid():
            agent = agn_form.save(commit=False)
            agent.created_by=request.user
            agent.is_context=True
            agent.save()
            project = pro_form.save(commit=False)
            project.agent = agent
            project.save()

            association_type = AgentAssociationType.objects.get(identifier="manager")
            fc_aa = AgentAssociation(
                is_associate=user_agent,
                has_associate=agent,
                association_type=association_type,
                state="active",
                )
            fc_aa.save()

            fc = EconomicAgent.objects.freedom_coop_projects()
            association_type = AgentAssociationType.objects.get(identifier="child")
            fc_aa = AgentAssociation(
                is_associate=agent,
                has_associate=fc,
                association_type=association_type,
                state="active",
                )
            fc_aa.save()

            return HttpResponseRedirect('/%s/%s/'
                % ('work/agent', agent.id))
    return HttpResponseRedirect("/work/your-projects/")


@login_required
def members_agent(request, agent_id):
    #import pdb; pdb.set_trace()
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    user_agent = get_agent(request)
    if not user_agent or not user_agent.is_participant or not user_agent.is_active_freedom_coop_member:
        return render(request, 'work/no_permission.html')

    user_is_agent = False
    if agent == user_agent:
        user_is_agent = True

    if user_agent.project_join_requests:
      for req in user_agent.project_join_requests.all():
        if req.project.agent == agent:
          user_agent.req = req
          break

    try:
        project = agent.project
    except:
        project = False

    if project:
        init = {"joining_style": project.joining_style, "visibility": project.visibility, "fobi_slug": project.fobi_slug }
        change_form = ProjectCreateForm(instance=agent, initial=init)
    else:
        change_form = ProjectCreateForm(instance=agent) #AgentCreateForm(instance=agent)

    nav_form = InternalExchangeNavForm(data=request.POST or None)
    if agent:
        if request.method == "POST":
            #import pdb; pdb.set_trace()
            if nav_form.is_valid():
                data = nav_form.cleaned_data
                ext = data["exchange_type"]
            return HttpResponseRedirect('/%s/%s/%s/%s/'
                % ('work/exchange', ext.id, 0, agent.id))
    user_form = None

    if not agent.username():
        init = {"username": agent.nick,}
        user_form = UserCreationForm(initial=init)
    has_associations = agent.all_has_associates()
    is_associated_with = agent.all_is_associates()
    assn_form = AssociationForm(agent=agent)

    headings = []
    member_hours_recent = []
    member_hours_stats = []
    individual_stats = []
    member_hours_roles = []
    roles_height = 400

    membership_request = agent.membership_request()
    entries = []
    fobi_name = 'None'

    if agent.is_individual():
        contributions = agent.given_events.filter(is_contribution=True)
        agents_stats = {}
        for ce in contributions:
            agents_stats.setdefault(ce.resource_type, Decimal("0"))
            agents_stats[ce.resource_type] += ce.quantity
        for key, value in agents_stats.items():
            individual_stats.append((key, value))
        individual_stats.sort(lambda x, y: cmp(y[1], x[1]))

    elif agent.is_context_agent():
        try:
          fobi_name = get_object_or_404(FormEntry, slug=agent.project.fobi_slug)
          entries = agent.project.join_requests.filter(agent__isnull=True)
        except:
          entries = []

        subs = agent.with_all_sub_agents()
        end = datetime.date.today()
        #end = end - datetime.timedelta(days=77)
        start =  end - datetime.timedelta(days=60)
        events = EconomicEvent.objects.filter(
            event_type__relationship="work",
            context_agent__in=subs,
            event_date__range=(start, end))

        if events:
            agents_stats = {}
            for event in events:
                agents_stats.setdefault(event.from_agent.name, Decimal("0"))
                agents_stats[event.from_agent.name] += event.quantity
            for key, value in agents_stats.items():
                member_hours_recent.append((key, value))
            member_hours_recent.sort(lambda x, y: cmp(y[1], x[1]))

        #import pdb; pdb.set_trace()

        ces = CachedEventSummary.objects.filter(
            event_type__relationship="work",
            context_agent__in=subs)

        if ces.count():
            agents_stats = {}
            for ce in ces:
                agents_stats.setdefault(ce.agent.name, Decimal("0"))
                agents_stats[ce.agent.name] += ce.quantity
            for key, value in agents_stats.items():
                member_hours_stats.append((key, value))
            member_hours_stats.sort(lambda x, y: cmp(y[1], x[1]))

            agents_roles = {}
            roles = [ce.quantity_label() for ce in ces]
            roles = list(set(roles))
            for ce in ces:
                if ce.quantity:
                    name = ce.agent.name
                    row = [name, ]
                    for i in range(0, len(roles)):
                        row.append(Decimal("0.0"))
                        key = ce.agent.name
                    agents_roles.setdefault(key, row)
                    idx = roles.index(ce.quantity_label()) + 1
                    agents_roles[key][idx] += ce.quantity
            headings = ["Member",]
            headings.extend(roles)
            for row in agents_roles.values():
                member_hours_roles.append(row)
            member_hours_roles.sort(lambda x, y: cmp(x[0], y[0]))
            roles_height = len(member_hours_roles) * 20

    #artwork = get_object_or_404(Artwork_Type, clas="Material")

    return render(request, "work/members_agent.html", {
        "agent": agent,
        "membership_request": membership_request,
        "photo_size": (128, 128),
        "change_form": change_form,
        "user_form": user_form,
        "nav_form": nav_form,
        "assn_form": assn_form,
        "user_agent": user_agent,
        "user_is_agent": user_is_agent,
        "has_associations": has_associations,
        "is_associated_with": is_associated_with,
        "headings": headings,
        "member_hours_recent": member_hours_recent,
        "member_hours_stats": member_hours_stats,
        "member_hours_roles": member_hours_roles,
        "individual_stats": individual_stats,
        "roles_height": roles_height,
        "help": get_help("members_agent"),
        "form_entries": entries,
        "fobi_name": fobi_name,
        #"artwork_pk": artwork.pk,
    })


@login_required
def edit_relations(request, agent_id):
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    user_agent = get_agent(request)
    #import pdb; pdb.set_trace()
    if user_agent in agent.managers():
        assn_form = AssociationForm(agent=agent,data=request.POST)
        if assn_form.is_valid():
            member_assn = AgentAssociation.objects.get(id=int(request.POST.get("member")))
            assn_type = AgentAssociationType.objects.get(id=int(request.POST.get("new_association_type")))
            member_assn.association_type = assn_type
            member_assn.save()

    return HttpResponseRedirect('/%s/%s/'
        % ('work/agent', agent.id))


@login_required
def change_your_project(request, agent_id):
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    user_agent = get_agent(request)
    if not user_agent:
        return render(request, 'work/no_permission.html')
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        try:
          project = agent.project
        except:
          project = False
        if not project:
          pro_form = ProjectCreateForm(request.POST)
          if pro_form.is_valid():
            project = pro_form.save(commit=False)
            project.agent = agent
            project.save()
        else:
          pro_form = ProjectCreateForm(instance=project, data=request.POST or None)

        agn_form = AgentCreateForm(instance=agent, data=request.POST or None)
        if pro_form.is_valid() and agn_form.is_valid():
            project = pro_form.save()
            data = agn_form.cleaned_data
            url = data["url"]
            if url and not url[0:3] == "http":
              data["url"] = "http://" + url
              agent.url = data["url"]
            #agent.project = project
            agent = agn_form.save(commit=False)
            agent.is_context = True
            agent.save()

    return HttpResponseRedirect('/%s/%s/'
        % ('work/agent', agent.id))




#   J O I N A P R O J E C T

from fobi.dynamic import assemble_form_class
from fobi.settings import GET_PARAM_INITIAL_DATA, DEBUG
from fobi.constants import (
    CALLBACK_BEFORE_FORM_VALIDATION,
    CALLBACK_FORM_VALID_BEFORE_SUBMIT_PLUGIN_FORM_DATA,
    CALLBACK_FORM_VALID, CALLBACK_FORM_VALID_AFTER_FORM_HANDLERS,
    CALLBACK_FORM_INVALID
)
from fobi.base import (
    fire_form_callbacks, run_form_handlers, form_element_plugin_registry,
    form_handler_plugin_registry, submit_plugin_form_data, get_theme,
    get_processed_form_data
)
#from fobi.base import (
#    FormHandlerPlugin, form_handler_plugin_registry, get_processed_form_data
#)

import simplejson as json
from django.utils.html import escape, escapejs

def joinaproject_request(request, form_slug = False):
    join_form = JoinRequestForm(data=request.POST or None)
    fobi_form = False
    cleaned_data = False
    form = False
    if form_slug:
      project = Project.objects.get(fobi_slug=form_slug)

      try:
        user_agent = request.user.agent.agent
        if user_agent and request.user.is_authenticated and user_agent.is_active_freedom_coop_member or request.user.is_staff:
          return joinaproject_request_internal(request, project.agent.id)
      except:
        user_agent = False

      if project.visibility != "public" and not user_agent:
        return HttpResponseRedirect('/%s/' % ('home'))

      fobi_slug = project.fobi_slug
      form_entry = FormEntry.objects.get(slug=fobi_slug)
      form_element_entries = form_entry.formelemententry_set.all()[:]
      form_entry.project = project

      # This is where the most of the magic happens. Our form is being built
      # dynamically.
      FormClass = assemble_form_class(
          form_entry,
          form_element_entries = form_element_entries,
          request = request
      )


    if request.method == "POST":
        #import pdb; pdb.set_trace()
        fobi_form = FormClass(request.POST, request.FILES)
        #form_element_entries = form_entry.formelemententry_set.all()[:]
        #field_name_to_label_map, cleaned_data = get_processed_form_data(
        #    fobi_form, form_element_entries,
        #)

        if join_form.is_valid():
            human = True
            data = join_form.cleaned_data
            type_of_user = data["type_of_user"]
            name = data["name"]
            surname = data["surname"]
            #description = data["description"]

            jn_req = join_form.save(commit=False)
            jn_req.project = project
            jn_req.save()

            #request.POST._mutable = True
            #request.POST['join_request'] = str(jn_req.pk)

            if form_slug:
              #fobi_form = FormClass(request.POST, request.FILES)

              # Fire pre form validation callbacks
              fire_form_callbacks(form_entry=form_entry, request=request, form=fobi_form, stage=CALLBACK_BEFORE_FORM_VALIDATION)
              if fobi_form.is_valid():
                #return HttpResponseRedirect('/%s/' % ('joinaprojectthanks'))

                # Fire form valid callbacks, before handling submitted plugin form data.
                fobi_form = fire_form_callbacks(
                    form_entry = form_entry,
                    request = request,
                    form = fobi_form,
                    stage = CALLBACK_FORM_VALID_BEFORE_SUBMIT_PLUGIN_FORM_DATA
                )

                # Fire plugin processors
                fobi_form = submit_plugin_form_data(form_entry=form_entry,
                                               request=request, form=fobi_form)

                # Fire form valid callbacks
                fobi_form = fire_form_callbacks(form_entry=form_entry,
                                           request=request, form=fobi_form,
                                           stage=CALLBACK_FORM_VALID)

                '''# Run all handlers
                handler_responses, handler_errors = run_form_handlers(
                    form_entry = form_entry,
                    request = request,
                    form = fobi_form,
                    form_element_entries = form_element_entries
                )

                # Warning that not everything went ok.
                if handler_errors:
                    for handler_error in handler_errors:
                        messages.warning(
                            request,
                            _("Error occured: {0}."
                              "").format(handler_error)
                        )
                '''

                # Fire post handler callbacks
                fire_form_callbacks(
                    form_entry = form_entry,
                    request = request,
                    form = fobi_form,
                    stage = CALLBACK_FORM_VALID_AFTER_FORM_HANDLERS
                    )

                #messages.info(
                #    request,
                #    _("Form {0} was submitted successfully.").format(form_entry.name)
                #)

                field_name_to_label_map, cleaned_data = get_processed_form_data(
                    fobi_form,
                    form_element_entries
                )

                #for key, value in cleaned_data.items():
                #    if key == "join_request": #isinstance(value, (datetime.datetime, datetime.date)):
                #        cleaned_data[key] = jn_req.pk #value.isoformat() if hasattr(value, 'isoformat') else value

                saved_form_data_entry = SavedFormDataEntry(
                    form_entry = form_entry,
                    user = request.user if request.user and request.user.pk else None,
                    form_data_headers = json.dumps(field_name_to_label_map),
                    saved_data = json.dumps(cleaned_data)
                    )
                saved_form_data_entry.save()
                jn = JoinRequest.objects.get(pk=jn_req.pk)
                jn.fobi_data = saved_form_data_entry
                #messages.info(
                #    request,
                #    _("JoinRequest {0} was submitted successfully. {1}").format(jn.fobi_data, saved_form_data_entry.pk)
                #)
                jn.save()

            # add relation candidate
            #ass_type = get_object_or_404(AgentAssociationType, identifier="participant")
            #if ass_type:
            #    fc_aa = AgentAssociation(
            #        is_associate=jn_req.agent,
            #        has_associate=jn_req.project.agent,
            #        association_type=ass_type,
            #        state="potential",
            #        )
            #    fc_aa.save()

            event_type = EventType.objects.get(relationship="todo")
            description = "Create an Agent and User for the Join Request from "
            description += name
            join_url = get_url_starter() + "/work/agent/" + str(jn_req.project.agent.id) +"/join-requests/"
            context_agent = jn_req.project.agent #EconomicAgent.objects.get(name__icontains="Membership Request")
            resource_types = EconomicResourceType.objects.filter(behavior="work")
            rts = resource_types.filter(
                Q(name__icontains="Admin")|
                Q(name__icontains="Coop")|
                Q(name__icontains="Work"))
            if rts:
                rt = rts[0]
            else:
                rt = resource_types[0]

            task = Commitment(
                event_type=event_type,
                description=description,
                resource_type=rt,
                context_agent=context_agent,
                url=join_url,
                due_date=datetime.date.today(),
                quantity=Decimal("1")
                )
            task.save()


            if notification:
                managers = jn_req.project.agent.managers()
                users = []
                for manager in managers:
                  if manager.user():
                    users.append(manager.user().user)
                if users:
                    site_name = get_site_name()
                    notification.send(
                        users,
                        "work_join_request",
                        {"name": name,
                        "surname": surname,
                        "type_of_user": type_of_user,
                        "description": description,
                        "site_name": site_name,
                        "join_url": join_url,
                        "context_agent": context_agent,
                        }
                    )

            return HttpResponseRedirect('/%s/'
                % ('joinaproject-thanks'))


    kwargs = {'initial': {'fobi_initial_data':form_slug} }
    fobi_form = FormClass(**kwargs)

    return render(request, "work/joinaproject_request.html", {
        "help": get_help("work_join_request"),
        "join_form": join_form,
        "fobi_form": fobi_form,
        "project": project,
        "post": escapejs(json.dumps(request.POST)),
    })


@login_required
def joinaproject_request_internal(request, agent_id = False):
    proj_agent = get_object_or_404(EconomicAgent, id=agent_id)
    project = proj_agent.project
    form_slug = project.fobi_slug
    join_form = JoinRequestInternalForm(data=request.POST or None)
    fobi_form = False
    cleaned_data = False
    form = False
    if form_slug:
      #project = Project.objects.get(fobi_slug=form_slug)
      fobi_slug = project.fobi_slug
      form_entry = FormEntry.objects.get(slug=fobi_slug)
      form_element_entries = form_entry.formelemententry_set.all()[:]
      #form_entry.project = project

      # This is where the most of the magic happens. Our form is being built
      # dynamically.
      FormClass = assemble_form_class(
          form_entry,
          form_element_entries = form_element_entries,
          request = request
      )
    else:
      return render(request, 'work/no_permission.html')

    if request.method == "POST":
        #import pdb; pdb.set_trace()
        fobi_form = FormClass(request.POST, request.FILES)
        #form_element_entries = form_entry.formelemententry_set.all()[:]
        #field_name_to_label_map, cleaned_data = get_processed_form_data(
        #    fobi_form, form_element_entries,
        #)

        if join_form.is_valid():
            human = True
            data = join_form.cleaned_data
            type_of_user = proj_agent.agent_type #data["type_of_user"]
            name = proj_agent.name #data["name"]
            #surname = proj_agent.surname #data["surname"]
            #description = data["description"]

            jn_req = join_form.save(commit=False)
            jn_req.project = project
            if request.user.agent.agent:
              jn_req.agent = request.user.agent.agent
            jn_req.save()

            #request.POST._mutable = True
            #request.POST['join_request'] = str(jn_req.pk)

            if form_slug:
              #fobi_form = FormClass(request.POST, request.FILES)

              # Fire pre form validation callbacks
              fire_form_callbacks(form_entry=form_entry, request=request, form=fobi_form, stage=CALLBACK_BEFORE_FORM_VALIDATION)
              if fobi_form.is_valid():
                #return HttpResponseRedirect('/%s/' % ('joinaprojectthanks'))

                # Fire form valid callbacks, before handling submitted plugin form data.
                fobi_form = fire_form_callbacks(
                    form_entry = form_entry,
                    request = request,
                    form = fobi_form,
                    stage = CALLBACK_FORM_VALID_BEFORE_SUBMIT_PLUGIN_FORM_DATA
                )

                # Fire plugin processors
                fobi_form = submit_plugin_form_data(form_entry=form_entry,
                                               request=request, form=fobi_form)

                # Fire form valid callbacks
                fobi_form = fire_form_callbacks(form_entry=form_entry,
                                           request=request, form=fobi_form,
                                           stage=CALLBACK_FORM_VALID)

                '''# Run all handlers
                handler_responses, handler_errors = run_form_handlers(
                    form_entry = form_entry,
                    request = request,
                    form = fobi_form,
                    form_element_entries = form_element_entries
                )

                # Warning that not everything went ok.
                if handler_errors:
                    for handler_error in handler_errors:
                        messages.warning(
                            request,
                            _("Error occured: {0}."
                              "").format(handler_error)
                        )
                '''

                # Fire post handler callbacks
                fire_form_callbacks(
                    form_entry = form_entry,
                    request = request,
                    form = fobi_form,
                    stage = CALLBACK_FORM_VALID_AFTER_FORM_HANDLERS
                    )

                #messages.info(
                #    request,
                #    _("Form {0} was submitted successfully.").format(form_entry.name)
                #)

                field_name_to_label_map, cleaned_data = get_processed_form_data(
                    fobi_form,
                    form_element_entries
                )

                saved_form_data_entry = SavedFormDataEntry(
                    form_entry = form_entry,
                    user = request.user if request.user and request.user.pk else None,
                    form_data_headers = json.dumps(field_name_to_label_map),
                    saved_data = json.dumps(cleaned_data)
                    )
                saved_form_data_entry.save()
                jn = JoinRequest.objects.get(pk=jn_req.pk)
                jn.fobi_data = saved_form_data_entry
                #messages.info(
                #    request,
                #    _("JoinRequest {0} was submitted successfully. {1}").format(jn.fobi_data, saved_form_data_entry.pk)
                #)
                jn.save()

            # add relation candidate
            if jn_req.agent:
                ass_type = get_object_or_404(AgentAssociationType, identifier="participant")
                if ass_type:
                  fc_aa = AgentAssociation(
                    is_associate=jn_req.agent,
                    has_associate=jn_req.project.agent,
                    association_type=ass_type,
                    state="potential",
                    )
                  fc_aa.save()

            description = "A new Join Request from OCP user "
            description += name
            join_url = ''

            '''event_type = EventType.objects.get(relationship="todo")
            join_url = get_url_starter() + "/work/agent/" + str(jn_req.project.agent.id) +"/join-requests/"
            context_agent = jn_req.project.agent #EconomicAgent.objects.get(name__icontains="Membership Request")
            resource_types = EconomicResourceType.objects.filter(behavior="work")
            rts = resource_types.filter(
                Q(name__icontains="Admin")|
                Q(name__icontains="Coop")|
                Q(name__icontains="Work"))
            if rts:
                rt = rts[0]
            else:
                rt = resource_types[0]

            task = Commitment(
                event_type=event_type,
                description=description,
                resource_type=rt,
                context_agent=context_agent,
                url=join_url,
                due_date=datetime.date.today(),
                quantity=Decimal("1")
                )
            task.save()'''


            if notification:
                managers = jn_req.project.agent.managers()
                users = []
                for manager in managers:
                  if manager.user():
                    users.append(manager.user().user)
                if users:
                    site_name = get_site_name()
                    notification.send(
                        users,
                        "work_join_request",
                        {"name": name,
                        #"surname": surname,
                        "type_of_user": type_of_user,
                        "description": description,
                        "site_name": site_name,
                        "join_url": join_url,
                        "context_agent": proj_agent,
                        }
                    )

            return HttpResponseRedirect('/%s/'
                % ('work/your-projects'))


    kwargs = {'initial': {'fobi_initial_data':form_slug} }
    fobi_form = FormClass(**kwargs)

    return render(request, "work/joinaproject_request_internal.html", {
        "help": get_help("work_join_request_internal"),
        "join_form": join_form,
        "fobi_form": fobi_form,
        "project": project,
        "post": escapejs(json.dumps(request.POST)),
    })



@login_required
def join_requests(request, agent_id):
    state = "new"
    state_form = RequestStateForm(
        initial={"state": "new",},
        data=request.POST or None)

    if request.method == "POST":
        if state_form.is_valid():
            data = state_form.cleaned_data
            state = data["state"]

    agent = EconomicAgent.objects.get(pk=agent_id)
    project = agent.project
    requests =  JoinRequest.objects.filter(state=state, project=project)
    agent_form = JoinAgentSelectionForm()

    fobi_slug = project.fobi_slug
    fobi_headers = []
    fobi_keys = []

    if fobi_slug and requests:
        form_entry = FormEntry.objects.get(slug=fobi_slug)
        req = requests[0]
        if req.fobi_data and req.fobi_data._default_manager:
            req.entries = req.fobi_data._default_manager.filter(pk=req.fobi_data.pk).select_related('form_entry')
            entry = req.entries[0]
            form_headers = json.loads(entry.form_data_headers)
            for val in form_headers:
                fobi_headers.append(form_headers[val])
                fobi_keys.append(val)

        for req in requests:
            if not req.agent and req.requested_username:
              try:
                req.possible_agent = EconomicAgent.objects.get(nick=req.requested_username)
              except:
                req.possible_agent = False
            if req.fobi_data and req.fobi_data._default_manager:
              req.entries = req.fobi_data._default_manager.filter(pk=req.fobi_data.pk).select_related('form_entry')
              entry = req.entries[0]
              req.data = json.loads(entry.saved_data)
              req.items = req.data.items()
              req.items_data = []
              for key in fobi_keys:
                req.items_data.append(req.data.get(key))
            else:
              req.entries = []

    return render(request, "work/join_requests.html", {
        "help": get_help("join_requests"),
        "requests": requests,
        "state_form": state_form,
        "state": state,
        "agent_form": agent_form,
        "project": project,
        "fobi_headers": fobi_headers,
    })


'''@login_required
def join_request(request, join_request_id):
    user_agent = get_agent(request)
    if not user_agent:
        return render(request, 'work/no_permission.html')
    mbr_req = get_object_or_404(JoinRequest, pk=join_request_id)
    init = {
        "name": " ".join([mbr_req.name, mbr_req.surname]),
        "nick": mbr_req.requested_username,
        #"description": mbr_req.description,
        "email": mbr_req.email_address,
        "url": mbr_req.website,
        }
    if mbr_req.type_of_user == "individual":
        at = AgentType.objects.filter(party_type="individual")
        if at:
            at = at[0]
            init["agent_type"] = at
    agent_form = AgentCreateForm(initial=init)
    nicks = '~'.join([
        agt.nick for agt in EconomicAgent.objects.all()])
    return render(request, "work/join_request.html", {
        "help": get_help("join_request"),
        "mbr_req": mbr_req,
        "agent_form": agent_form,
        "user_agent": user_agent,
        "nicks": nicks,
    })
'''

@login_required
def decline_request(request, join_request_id):
    mbr_req = get_object_or_404(JoinRequest, pk=join_request_id)
    mbr_req.state = "declined"
    mbr_req.save()
    if mbr_req.agent and mbr_req.project:
        # modify relation to active
        ass_type = AgentAssociationType.objects.get(identifier="participant")
        ass, created = AgentAssociation.objects.get_or_create(is_associate=mbr_req.agent, has_associate=mbr_req.project.agent, association_type=ass_type)
        ass.state = "potential"
        ass.save()
    return HttpResponseRedirect('/%s/%s/%s/'
        % ('work/agent', mbr_req.project.agent.id, 'join-requests'))

@login_required
def undecline_request(request, join_request_id):
    mbr_req = get_object_or_404(JoinRequest, pk=join_request_id)
    mbr_req.state = "new"
    mbr_req.save()
    return HttpResponseRedirect('/%s/%s/%s/'
        % ('work/agent', mbr_req.project.agent.id, 'join-requests'))

@login_required
def delete_request(request, join_request_id):
    mbr_req = get_object_or_404(JoinRequest, pk=join_request_id)
    mbr_req.delete()
    if mbr_req.agent:
      pass # delete user and agent?

    return HttpResponseRedirect('/%s/%s/%s/'
        % ('work/agent', mbr_req.project.agent.id, 'join-requests'))

@login_required
def accept_request(request, join_request_id):
    mbr_req = get_object_or_404(JoinRequest, pk=join_request_id)
    mbr_req.state = "accepted"
    mbr_req.save()

    # modify relation to active
    association_type = AgentAssociationType.objects.get(identifier="participant")
    try:
      association, created = AgentAssociation.objects.get_or_create(is_associate=mbr_req.agent, has_associate=mbr_req.project.agent, association_type=association_type)
      association.state = "active"
      association.save()
    except:
      pass

    return HttpResponseRedirect('/%s/%s/%s/'
        % ('work/agent', mbr_req.project.agent.id, 'join-requests'))


from itertools import chain

@login_required
def create_account_for_join_request(request, join_request_id):
    if request.method == "POST":
        jn_req = get_object_or_404(JoinRequest, pk=join_request_id)
        #import pdb; pdb.set_trace()
        form = ProjectAgentCreateForm(prefix=jn_req.form_prefix(), data=request.POST or None)
        if form.is_valid():
            data = form.cleaned_data
            agent = form.save(commit=False)
            agent.created_by=request.user
            if not agent.is_individual():
                agent.is_context=True
            agent.save()
            jn_req.agent = agent
            jn_req.save()
            project = jn_req.project
            # add relation candidate
            ass_type = get_object_or_404(AgentAssociationType, identifier="participant")
            if ass_type:
                aa = AgentAssociation(
                    is_associate=agent,
                    has_associate=project.agent,
                    association_type=ass_type,
                    state="potential",
                    )
                aa.save()
            password = data["password"]
            if password:
                username = data["nick"]
                email = data["email"]
                if username:
                    user = User(
                        username=username,
                        email=email,
                        )
                    user.set_password(password)
                    user.save()
                    au = AgentUser(
                        agent = agent,
                        user = user)
                    au.save()
                    #agent.request_faircoin_address()

                    name = data["name"]
                    if notification:
                        managers = project.agent.managers()
                        users = [agent.user().user,]
                        for manager in managers:
                            if manager.user():
                                users.append(manager.user().user)
                        #users = User.objects.filter(is_staff=True)
                        if users:
                            #allusers = chain(users, agent)
                            #users = list(users)
                            #users.append(agent.user)
                            site_name = get_site_name()
                            notification.send(
                                users,
                                "work_new_account",
                                {"name": name,
                                "username": username,
                                "password": password,
                                "site_name": site_name,
                                "context_agent": project.agent,
                                }
                            )

            return HttpResponseRedirect('/%s/%s/%s/'
                % ('work/agent', project.agent.id, 'join-requests'))

    return HttpResponseRedirect('/%s/%s/%s/'
        % ('work/agent', jn_req.project.agent.id, 'join-requests'))

@login_required
def join_project(request, project_id):
    if request.method == "POST":
        project = get_object_or_404(EconomicAgent, pk=project_id)
        user_agent = get_agent(request)
        association_type = AgentAssociationType.objects.get(identifier="participant")
        aa = AgentAssociation(
            is_associate=user_agent,
            has_associate=project,
            association_type=association_type,
            state="active",
            )
        aa.save()

    return HttpResponseRedirect("/work/your-projects/")


@login_required
def project_feedback(request, agent_id, join_request_id):
    user_agent = get_agent(request)
    agent = get_object_or_404(EconomicAgent, pk=agent_id)
    jn_req = get_object_or_404(JoinRequest, pk=join_request_id)
    project = agent.project
    allowed = False
    if user_agent and jn_req:
      if user_agent.is_staff() or user_agent in agent.managers():
        allowed = True
      elif jn_req.agent == request.user.agent.agent: #in user_agent.joinaproject_requests():
        allowed = True
    if not allowed:
        return render(request, 'work/no_permission.html')

    fobi_slug = project.fobi_slug
    fobi_headers = []
    fobi_keys = []

    if fobi_slug:
        form_entry = FormEntry.objects.get(slug=fobi_slug)
        #req = jn_req
        if jn_req.fobi_data:
            jn_req.entries = jn_req.fobi_data._default_manager.filter(pk=jn_req.fobi_data.pk) #.select_related('form_entry')
            jn_req.entry = jn_req.entries[0]
            jn_req.form_headers = json.loads(jn_req.entry.form_data_headers)
            for val in jn_req.form_headers:
                fobi_headers.append(jn_req.form_headers[val])
                fobi_keys.append(val)

            jn_req.data = json.loads(jn_req.entry.saved_data)
            #jn_req.tworows = two_dicts_to_string(jn_req.form_headers, jn_req.data, 'th', 'td')
            jn_req.items = jn_req.data.items()
            jn_req.items_data = []
            for key in fobi_keys:
              jn_req.items_data.append({"key": jn_req.form_headers[key], "val": jn_req.data.get(key)})

    return render(request, "work/join_request_with_comments.html", {
        "help": get_help("project_feedback"),
        "jn_req": jn_req,
        "user_agent": user_agent,
        "agent": agent,
        "fobi_headers": fobi_headers,
    })




def validate_nick(request):
    #import pdb; pdb.set_trace()
    answer = True
    error = ""
    data = request.GET
    values = data.values()
    if values:
        nick = values[0]
        try:
            user = EconomicAgent.objects.get(nick=nick)
            error = "ID already taken"
        except EconomicAgent.DoesNotExist:
            pass
        if not error:
            username = nick
            try:
                user = User.objects.get(username=username)
                error = "Username already taken"
            except User.DoesNotExist:
                pass
            if not error:
                val = validators.RegexValidator(r'^[\w.@+-]+$',
                                            _('Enter a valid username. '
                                                'This value may contain only letters, numbers '
                                               'and @/./+/-/_ characters.'), 'invalid')
                try:
                    error = val(username)
                except ValidationError:
                    error = "Error: May only contain letters, numbers, and @/./+/-/_ characters."

    if error:
        answer = error
    response = simplejson.dumps(answer, ensure_ascii=False)
    return HttpResponse(response, content_type="text/json-comment-filtered")


def validate_username(request):
    #import pdb; pdb.set_trace()
    answer = True
    error = ""
    data = request.GET
    values = data.values()
    if values:
        username = values[0]
        try:
            user = User.objects.get(username=username)
            error = "Username already taken"
        except User.DoesNotExist:
            pass
        if not error:
            val = validators.RegexValidator(r'^[\w.@+-]+$',
                                        _('Enter a valid username. '
                                            'This value may contain only letters, numbers '
                                            'and @/./+/-/_ characters.'), 'invalid')
            try:
                error = val(username)
            except ValidationError:
                error = "Error: May only contain letters, numbers, and @/./+/-/_ characters."
    if error:
        answer = error
    response = simplejson.dumps(answer, ensure_ascii=False)
    return HttpResponse(response, content_type="text/json-comment-filtered")



@login_required
def connect_agent_to_join_request(request, agent_id, join_request_id):
    mbr_req = get_object_or_404(JoinRequest, pk=join_request_id)
    project_agent = get_object_or_404(EconomicAgent, pk=agent_id)
    if request.method == "POST":
        agent_form = JoinAgentSelectionForm(data=request.POST)
        if agent_form.is_valid():
            data = agent_form.cleaned_data
            #import pdb; pdb.set_trace()
            agent = data["created_agent"]
            mbr_req.agent=agent
            mbr_req.state = "new"
            mbr_req.save()

    return HttpResponseRedirect('/%s/%s/%s/'
        % ('work/agent', project_agent.id, 'join-requests'))

from six import text_type, PY3
from django.utils.encoding import force_text

def safe_text(text):
    """
    Safe text (encode).

    :return str:
    """
    if PY3:
        return force_text(text, encoding='utf-8')
    else:
        return force_text(text, encoding='utf-8').encode('utf-8')

def two_dicts_to_string(headers, data, html_element1='th', html_element2='td'):
    """
    Takes two dictionaries, assuming one contains a mapping keys to titles
    and another keys to data. Joins as string and returns wrapped into
    HTML "p" tag.
    """
    formatted_data = [
        (value, data.get(key, '')) for key, value in list(headers.items())
        ]
    return "".join(
        ["<tr><{0}>{1}</{2}><{3}>{4}</{5}></tr>".format(html_element1, safe_text(key), html_element1, html_element2,
                                      safe_text(value), html_element2)
         for key, value in formatted_data]
        )



'''
@login_required
def create_project_user_and_agent(request, agent_id):
    #import pdb; pdb.set_trace()
    project_agent = get_object_or_404(EconomicAgent, id=agent_id)
    if not project_agent.managers: # or not request.user.agent.agent in project_agent.managers:
        return render(request, 'valueaccounting/no_permission.html')
    user_form = UserCreationForm(data=request.POST or None)
    agent_form = AgentForm(data=request.POST or None)
    agent_selection_form = AgentSelectionForm()
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        sa_id = request.POST.get("selected_agent")
        agent = None
        if sa_id:
            agent = EconomicAgent.objects.get(id=sa_id)
        if agent_form.is_valid():
            nick = request.POST.get("nick")
            description = request.POST.get("description")
            url = request.POST.get("url")
            address = request.POST.get("address")
            email = request.POST.get("email")
            agent_type_id = request.POST.get("agent_type")
            errors = False
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            username = request.POST.get("username")
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")  or ""
            if password1:
                if password1 != password2:
                    errors = True
                if not username:
                    errors = True
                user_form.is_valid()
            if not errors:
                if agent:
                    agent.description = description
                    agent.url = url
                    agent.address = address
                    if agent_type_id:
                        if agent.agent_type.id != agent_type_id:
                            agent_type = AgentType.objects.get(id=agent_type_id)
                            agent.agent_type = agent_type
                    if not agent.email:
                        agent.email = email
                else:
                    if nick and first_name:
                        try:
                            agent = EconomicAgent.objects.get(nick=nick)
                            errors = True
                        except EconomicAgent.DoesNotExist:
                            pass
                    else:
                        errors = True
                    if not errors:
                        name = " ".join([first_name, last_name])
                        agent_type = AgentType.objects.get(id=agent_type_id)
                        agent = EconomicAgent(
                            nick = nick,
                            name = name,
                            description = description,
                            url = url,
                            address = address,
                            agent_type = agent_type,
                        )
                if not errors:
                    if user_form.is_valid():
                        agent.created_by=request.user
                        agent.save()
                        user = user_form.save(commit=False)
                        user.first_name = request.POST.get("first_name")
                        user.last_name = request.POST.get("last_name")
                        user.email = request.POST.get("email")
                        user.save()
                        au = AgentUser(
                            agent = agent,
                            user = user)
                        au.save()
                        return HttpResponseRedirect('/%s/%s/'
                            % ('accounting/agent', agent.id))

    return render(request, "work/create_project_user_and_agent.html", {
        "user_form": user_form,
        "agent_form": agent_form,
        "agent_selection_form": agent_selection_form,
    })

'''



#    E X C H A N G E S   A L L

@login_required
def exchanges_all(request, agent_id): #all types of exchanges for one context agent
    #import pdb; pdb.set_trace()
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    today = datetime.date.today()
    end =  today
    start = today - datetime.timedelta(days=365)
    init = {"start_date": start, "end_date": end}
    dt_selection_form = DateSelectionForm(initial=init, data=request.POST or None)
    et_give = EventType.objects.get(name="Give")
    et_receive = EventType.objects.get(name="Receive")
    context_ids = [c.id for c in agent.related_all_agents()]
    context_ids.append(agent.id)
    ets = ExchangeType.objects.filter(context_agent__id__in=context_ids) #all()
    event_ids = ""
    select_all = True
    selected_values = "all"

    nav_form = ExchangeNavForm(agent=agent, data=request.POST or None)

    gen_ext = Ocp_Record_Type.objects.get(clas='ocp_exchange')
    usecases = Ocp_Record_Type.objects.filter(parent__id=gen_ext.id).exclude( Q(exchange_type__isnull=False), Q(exchange_type__context_agent__isnull=False), ~Q(exchange_type__context_agent__id__in=context_ids) ) #UseCase.objects.filter(identifier__icontains='_xfer')
    outypes = Ocp_Record_Type.objects.filter( Q(exchange_type__isnull=False), Q(exchange_type__context_agent__isnull=False), ~Q(exchange_type__context_agent__id__in=context_ids) )
    outchilds_ids = []
    for tp in outypes:
      desc = tp.get_descendants(True)
      outchilds_ids.extend([ds.id for ds in desc])
    exchange_types = Ocp_Record_Type.objects.filter(lft__gt=gen_ext.lft, rght__lt=gen_ext.rght, tree_id=gen_ext.tree_id).exclude(id__in=outchilds_ids) #.exclude(Q(exchange_type__isnull=False), ~Q(exchange_type__context_agent__id__in=context_ids))
    #usecase_ids = [uc.id for uc in usecases]

    ext_form = ContextExchangeTypeForm(agent=agent, data=request.POST or None)
    #unit_types = Ocp_Unit_Type.objects.all()

    Rtype_form = NewResourceTypeForm(agent=agent, data=request.POST or None)
    Stype_form = NewSkillTypeForm(agent=agent, data=request.POST or None)

    if request.method == "POST":
        #import pdb; pdb.set_trace()
        new_exchange = request.POST.get("new_exchange")
        if new_exchange:
            if nav_form.is_valid():
                data = nav_form.cleaned_data
                if hasattr(data["used_exchange_type"], 'id'):
                  old_ext = ExchangeType.objects.get(id=data["used_exchange_type"].id)
                  if old_ext.id:
                    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                      % ('work/agent', agent.id, 'exchange-logging-work', old_ext.id, 0))

                if hasattr(data["exchange_type"], 'id'):
                  gen_ext = Ocp_Record_Type.objects.get(id=data["exchange_type"].id)
                  ext = gen_ext.exchange_type
                  if ext:
                    gen_rt = None
                    gen_sk = None

                    if hasattr(data["resource_type"], 'id'): # we are creating a new exchange type and ext is the parent?
                      gen_rt = Ocp_Artwork_Type.objects.get(id=data["resource_type"].id)

                    if hasattr(data["skill_type"], 'id'):
                      gen_sk = Ocp_Skill_Type.objects.get(id=data["skill_type"].id)

                    #import pdb; pdb.set_trace()

                    if gen_rt and gen_ext.ocp_artwork_type and gen_ext.ocp_artwork_type == gen_rt: # we have the related RT in the ET! do nothing.
                      return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                              % ('work/agent', agent.id, 'exchange-logging-work', ext.id, 0))
                    if gen_sk and gen_ext.ocp_skill_type and gen_ext.ocp_skill_type == gen_sk: # we have the related RT in the ET! do nothing.
                      return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                              % ('work/agent', agent.id, 'exchange-logging-work', ext.id, 0))

                    name = None
                    narr = gen_ext.name.split(' ')
                    if len(narr) > 0:
                      name = narr[0] # get only first word of general record type ?
                    if gen_sk:
                      if gen_sk.gerund:
                        name += ' '+gen_sk.gerund.title()
                      else:
                        name += ' '+gen_sk.name
                    if gen_rt:
                      name += ' '+gen_rt.name

                    agnt = None
                    if gen_rt and hasattr(gen_rt.resource_type, 'context_agent'):
                      agnt = gen_rt.resource_type.context_agent
                    elif gen_sk and hasattr(gen_sk.resource_type, 'context_agent'):
                      agnt = gen_sk.resource_type.context_agent
                    elif ext.context_agent:
                      agnt = agent #ext.context_agent
                    else:
                      agnt = agent

                    uc = ext.use_case
                    if name and uc:
                      try:
                        new_ext = ExchangeType.objects.get(name=name)
                        if new_ext:
                          if new_ext.context_agent and not new_ext.context_agent == agnt:
                            if agnt.parent():
                              new_ext.context_agent = agnt.parent()
                            else:
                              new_ext.context_agent = agnt

                            new_ext.edited_by = request.user
                            new_ext.save() # TODO check if the new_ext is reached by the agent related contexts
                          return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                            % ('work/agent', agent.id, 'exchange-logging-work', new_ext.id, 0))
                      except:
                        #pass
                        new_ext = ExchangeType(
                          name=name,
                          use_case=uc,
                          created_by=request.user,
                          created_date=datetime.date.today(),
                          context_agent=agnt
                        )
                        new_ext.save() # here we get an id

                      new_rec = Ocp_Record_Type(gen_ext)
                      new_rec.pk = None
                      new_rec.id = None
                      new_rec.name = name
                      new_rec.exchange_type = new_ext
                      new_rec.ocpRecordType_ocp_artwork_type = gen_rt
                      new_rec.ocp_skill_type = gen_sk
                      # mptt: insert_node(node, target, position='last-child', save=False)
                      new_rec = Ocp_Record_Type.objects.insert_node(new_rec, gen_ext, 'last-child', True)

                      inherited = False
                      for tr in ext.transfer_types.all():
                        if tr.inherit_types == True:
                          inherited = True
                      if inherited: # any of the transfer_types has inherit_types?
                        for tr in ext.transfer_types.all():
                          new_tr = TransferType.objects.get(pk=tr.pk)
                          new_tr.pk = None
                          new_tr.id = None
                          new_tr.exchange_type = new_ext
                          new_tr.created_by = request.user
                          new_tr.created_date = datetime.date.today()
                          narr = tr.name.split(' ')
                          nam = ' '.join(narr[:-1]) # substitute the last word in transfer name for the resource type name
                          new_tr.name = nam
                          if gen_sk:
                            new_tr.name += ' - '+gen_sk.name
                          if gen_rt:
                            new_tr.name += ' - '+gen_rt.name

                          new_tr.save()

                          if tr.inherit_types == True: # provisional inheriting of the facet_value assigned in ocp_artwork_type tree
                            inherited = True
                            # its just-in-case as a fail saver (the resource types will be retrieved via exchange_type)
                            # mptt: get_ancestors(ascending=False, include_self=False)
                            if gen_rt:
                              parids = [p.id for p in gen_rt.get_ancestors(True, True)] # careful! these are general.Type and the upper level
                              pars = gen_rt.get_ancestors(True)                         # 'Artwork' is not in Artwork_Type nor Ocp_Artwork_Type
                              for par in pars:
                                if par.clas != 'Artwork':
                                  pr = Ocp_Artwork_Type.objects.get(id=par.id)
                                  if pr.facet_value:
                                    ttfv, created = TransferTypeFacetValue.objects.get_or_create(
                                      transfer_type=new_tr,
                                      facet_value=pr.facet_value,
                                      # defaults={},
                                    )
                                    if ttfv:
                                      new_tr.facet_values.add(ttfv)
                                      break
                            if gen_sk:
                              parids = [p.id for p in gen_sk.get_ancestors(True, True)] # careful! these are general.Job
                              pars = gen_sk.get_ancestors(True)
                              for par in pars:
                                  pr = Ocp_Skill_Type.objects.get(id=par.id)
                                  if pr.facet_value:
                                    ttfv, created = TransferTypeFacetValue.objects.get_or_create(
                                      transfer_type=new_tr,
                                      facet_value=pr.facet_value,
                                      # defaults={},
                                    )
                                    if ttfv:
                                      new_tr.facet_values.add(ttfv)
                                      break
                          else:
                            old_fvs = tr.facet_values.all()
                            new_tr.facet_values = old_fvs
                            #import pdb; pdb.set_trace()

                        # end for tr in ext.transfer_types.all()
                        return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                              % ('work/agent', agent.id, 'exchange-logging-work', new_ext.id, 0))

                      else: # not inherited, rise error
                        raise ValidationError("No transfer inheriting types in this exchange type! "+ext.name)

                    else: # end if name and uc:
                      raise ValidationError("Bad new name ("+name+") or no use-case in the parent exchange type! "+ext.name)

                    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                        % ('work/agent', agent.id, 'exchange-logging-work', ext.id, 0))

                  else: # endif ext
                    # the ocp record type still not have an ocp exchange type, create it? TODO
                    pass

                  #return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                  #  % ('work/agent', agent.id, 'exchange-logging-work', ext.id, gen_rt.id)) # ¿ use the exchange id for a resource id ?

                else: # endif hasattr(data["exchange_type"], 'id'):
                  #nav_form.add_error('exchange_type', _("No exchange type selected"))
                  pass #raise ValidationError("No exchange type selected")

            else: # nav_form is not valid
              pass #raise ValidationError(nav_form.errors)

        # there's no new_exchange, is it a new resource type?
        new_resource_type = request.POST.get("new_resource_type")
        if new_resource_type:
            if Rtype_form.is_valid():
                data = Rtype_form.cleaned_data
                if hasattr(data["resource_type"], 'id'):
                  parent_rt = Ocp_Artwork_Type.objects.get(id=data["resource_type"].id)
                  if parent_rt.id:
                    out = None
                    if hasattr(data["unit_type"], 'id'):
                      gut = Ocp_Unit_Type.objects.get(id=data["unit_type"].id)
                      out = gut.ocpUnitType_ocp_unit
                    if hasattr(data, "substitutable"):
                      substi = data["substitutable"]
                    else:
                      substi = False
                    new_rt = EconomicResourceType(
                      name=data["name"],
                      description=data["description"],
                      unit=out,
                      price_per_unit=data["price_per_unit"],
                      substitutable=substi,
                      context_agent=data["context_agent"],
                      url=data["url"],
                      photo_url=data["photo_url"],
                      parent=data["parent"],
                      created_by=request.user,
                    )
                    #try:
                    new_rt.save()
                    #except:
                    #  raise ValidationError('Cannot save new resource type:'+str(new_oat)+' Parent:'+str(parent_rt))

                    # mptt: get_ancestors(ascending=False, include_self=False)
                    ancs = parent_rt.get_ancestors(True, True)
                    for an in ancs:
                      if an.clas != 'Artwork':
                        an = Ocp_Artwork_Type.objects.get(id=an.id)
                        if an.resource_type:
                          for fv in an.resource_type.facets.all():
                            new_rtfv = ResourceTypeFacetValue(
                              resource_type=new_rt,
                              facet_value=fv.facet_value
                            )
                            new_rtfv.save()
                          break
                        elif an.facet_value:
                          new_rtfv = ResourceTypeFacetValue(
                              resource_type=new_rt,
                              facet_value=an.facet_value
                          )
                          new_rtfv.save()
                          break

                    rel_material = None
                    rel_nonmaterial = None
                    if hasattr(data["related_type"], 'id'):
                      rrt = Ocp_Artwork_Type.objects.get(id=data["related_type"].id)
                      # mptt: get_ancestors(ascending=False, include_self=False)
                      rrt_ancs = rrt.get_ancestors(False, True)
                      for an in rrt_ancs: # see if is child of material or non-material
                        if an.clas == 'Material':
                          mat = Material_Type.objects.get(id=rrt.id)
                          rel_material = mat
                          break
                        if an.clas == 'Nonmaterial':
                          non = Nonmaterial_Type.objects.get(id=rrt.id)
                          rel_nonmaterial = non
                          break

                    new_oat = Ocp_Artwork_Type(
                      name=data["name"],
                      description=data["description"],
                      resource_type=new_rt,
                      ocpArtworkType_material_type=rel_material,
                      ocpArtworkType_nonmaterial_type=rel_nonmaterial,
                    )
                    # mptt: insert_node(node, target, position='last-child', save=False)
                    try:
                      new_res = Ocp_Artwork_Type.objects.insert_node(new_oat, parent_rt, 'last-child', True)
                    except:
                      raise ValidationError('Cannot insert node:'+str(new_oat)+' Parent:'+str(parent_rt))


                    nav_form = ExchangeNavForm(agent=agent, data=None)
                    Rtype_form = NewResourceTypeForm(agent=agent, data=None)
                    Stype_form = NewSkillTypeForm(agent=agent, data=None)

                  else: # have no parent_type id
                    pass
                else: # have no parent resource field
                  pass
            else:
                pass #raise ValidationError(Rtype_form.errors)

        edit_resource_type = request.POST.get("edit_resource_type")
        if edit_resource_type:
            if Rtype_form.is_valid():
                data = Rtype_form.cleaned_data
                if hasattr(data["resource_type"], 'id'):
                  parent_rt = Ocp_Artwork_Type.objects.get(id=data["resource_type"].id)
                  if parent_rt.id:
                    out = None
                    if hasattr(data["unit_type"], 'id'):
                      gut = Ocp_Unit_Type.objects.get(id=data["unit_type"].id)
                      out = gut.ocpUnitType_ocp_unit
                    edid = request.POST.get("edid")
                    if edid == '':
                      raise ValidationError("Missing edid!")
                    else:
                      #raise ValidationError("Lets edit "+edid)
                      idar = edid.split('_')
                      if idar[0] == "Rid":
                        grt = Ocp_Artwork_Type.objects.get(id=idar[1])
                        grt.name = data["name"]
                        grt.description = data["description"]
                        moved = False
                        if not grt.parent == parent_rt:
                          # mptt: move_to(target, position='first-child')
                          grt.move_to(parent_rt, 'last-child')
                          moved = True

                        rel_material = None
                        rel_nonmaterial = None
                        if hasattr(data["related_type"], 'id'):
                          rrt = Ocp_Artwork_Type.objects.get(id=data["related_type"].id)
                          # mptt: get_ancestors(ascending=False, include_self=False)
                          rrt_ancs = rrt.get_ancestors(False, True)
                          for an in rrt_ancs: # see if is child of material or non-material
                            if an.clas == 'Material':
                              mat = Material_Type.objects.get(id=rrt.id)
                              rel_material = mat
                              break
                            if an.clas == 'Nonmaterial':
                              non = Nonmaterial_Type.objects.get(id=rrt.id)
                              rel_nonmaterial = non
                              break
                          grt.ocpArtworkType_material_type = rel_material
                          grt.ocpArtworkType_nonmaterial_type = rel_nonmaterial

                        grt.save()

                        if not grt.resource_type:
                          #pass #raise ValidationError("There's no resource type! create it?")
                          if hasattr(data, "substitutable"):
                            substi = data["substitutable"]
                          else:
                            substi = False
                          new_rt = EconomicResourceType(
                            name=data["name"],
                            description=data["description"],
                            unit=out,
                            price_per_unit=data["price_per_unit"],
                            substitutable=substi,
                            context_agent=data["context_agent"],
                            url=data["url"],
                            photo_url=data["photo_url"],
                            parent=data["parent"],
                            created_by=request.user,
                          )
                          new_rt.save()
                          grt.resource_type = new_rt
                          grt.save()

                          # mptt: get_ancestors(ascending=False, include_self=False)
                          ancs = parent_rt.get_ancestors(True, True)
                          for an in ancs:
                            if an.clas != 'Artwork':
                              an = Ocp_Artwork_Type.objects.get(id=an.id)
                              if an.resource_type:
                                for fv in an.resource_type.facets.all():
                                  new_rtfv = ResourceTypeFacetValue(
                                    resource_type=new_rt,
                                    facet_value=fv.facet_value
                                  )
                                  new_rtfv.save()
                                break
                              elif an.facet_value:
                                new_rtfv = ResourceTypeFacetValue(
                                    resource_type=new_rt,
                                    facet_value=an.facet_value
                                )
                                new_rtfv.save()
                                break

                        else:
                          rt = grt.resource_type;
                          rt.name = data["name"]
                          rt.description = data["description"]
                          rt.unit = out
                          rt.price_per_unit = data["price_per_unit"]
                          rt.substitutable = data["substitutable"]
                          rt.context_agent = data["context_agent"]
                          rt.url = data["url"]
                          rt.photo_url = data["photo_url"]
                          rt.parent = data["parent"]
                          rt.edited_by = request.user
                          if moved:
                            old_rtfvs = ResourceTypeFacetValue.objects.filter(resource_type=rt)
                            for rtfv in old_rtfvs:
                              rtfv.delete()
                            # mptt: get_ancestors(ascending=False, include_self=False)
                            ancs = parent_rt.get_ancestors(True, True)
                            for an in ancs:
                              if an.clas != 'Artwork':
                                an = Ocp_Artwork_Type.objects.get(id=an.id)
                                if an.resource_type:
                                  for fv in an.resource_type.facets.all():
                                    new_rtfv = ResourceTypeFacetValue(
                                      resource_type=rt,
                                      facet_value=fv.facet_value
                                    )
                                    new_rtfv.save()
                                  break
                                elif an.facet_value:
                                  new_rtfv = ResourceTypeFacetValue(
                                      resource_type=rt,
                                      facet_value=an.facet_value
                                  )
                                  new_rtfv.save()
                                  break
                          rt.save()

                        nav_form = ExchangeNavForm(agent=agent, data=None)
                        Rtype_form = NewResourceTypeForm(agent=agent, data=None)
                        Stype_form = NewSkillTypeForm(agent=agent, data=None)

                      else: # is not Rid
                        pass

                  else: # have no parent_type id
                    pass
                else: # have no parent resource field
                  pass

        # there's no new_resource_type = request.POST.get("new_resource_type")
        new_skill_type = request.POST.get("new_skill_type")
        if new_skill_type:
            if Stype_form.is_valid():
                #raise ValidationError("New resource type, valid")
                data = Stype_form.cleaned_data
                if hasattr(data["parent_type"], 'id'):
                  parent_rt = Ocp_Skill_Type.objects.get(id=data["parent_type"].id)
                  if parent_rt.id:
                    out = None
                    if hasattr(data["unit_type"], 'id'):
                      gut = Ocp_Unit_Type.objects.get(id=data["unit_type"].id)
                      out = gut.ocpUnitType_ocp_unit
                    new_rt = EconomicResourceType(
                      name=data["name"],
                      description=data["description"],
                      unit=out,
                      price_per_unit=data["price_per_unit"],
                      substitutable=False, #data["substitutable"],
                      context_agent=data["context_agent"],
                      url=data["url"],
                      photo_url=data["photo_url"],
                      #parent=data["parent"],
                      created_by=request.user,
                      behavior="work",
                      inventory_rule="never",
                    )
                    new_rt.save()

                    # mptt: get_ancestors(ascending=False, include_self=False)
                    ancs = parent_rt.get_ancestors(True, True)
                    for an in ancs:
                      #if an.clas != 'Artwork':
                        an = Ocp_Skill_Type.objects.get(id=an.id)
                        if an.resource_type:
                          for fv in an.resource_type.facets.all():
                            new_rtfv = ResourceTypeFacetValue(
                              resource_type=new_rt,
                              facet_value=fv.facet_value
                            )
                            new_rtfv.save()
                          break
                        elif an.facet_value:
                          new_rtfv = ResourceTypeFacetValue(
                              resource_type=new_rt,
                              facet_value=an.facet_value
                          )
                          new_rtfv.save()
                          break

                    new_oat = Ocp_Skill_Type(
                      name=data["name"],
                      verb=data["verb"],
                      gerund=data["gerund"],
                      description=data["description"],
                      resource_type=new_rt,
                      ocp_artwork_type=data["related_type"],
                    )
                    # mptt: insert_node(node, target, position='last-child', save=False)
                    new_ski = Ocp_Skill_Type.objects.insert_node(new_oat, parent_rt, 'last-child', True)

                    nav_form = ExchangeNavForm(agent=agent, data=None)
                    Rtype_form = NewResourceTypeForm(agent=agent, data=None)
                    Stype_form = NewSkillTypeForm(agent=agent, data=None)

                  else: # have no parent_type id
                    pass
                else: # have no parent resource field
                  pass
            else:
                pass #raise ValidationError(Rtype_form.errors)


        edit_skill_type = request.POST.get("edit_skill_type")
        if edit_skill_type:
            if Stype_form.is_valid():
                data = Stype_form.cleaned_data
                if hasattr(data["parent_type"], 'id'):
                  parent_st = Ocp_Skill_Type.objects.get(id=data["parent_type"].id)
                  if parent_st.id:
                    out = None
                    if hasattr(data["unit_type"], 'id'):
                      gut = Ocp_Unit_Type.objects.get(id=data["unit_type"].id)
                      out = gut.ocpUnitType_ocp_unit
                    edid = request.POST.get("edid")
                    if edid == '':
                      raise ValidationError("Missing id of the edited skill! (edid)")
                    else:
                      #raise ValidationError("Lets edit "+edid)
                      idar = edid.split('_')
                      if idar[0] == "Sid":
                        grt = Ocp_Skill_Type.objects.get(id=idar[1])
                        grt.name = data["name"]
                        grt.description = data["description"]
                        grt.verb = data["verb"]
                        grt.gerund = data["gerund"]

                        moved = False
                        if not grt.parent == parent_st:
                          # mptt: move_to(target, position='first-child')
                          grt.move_to(parent_st, 'last-child')
                          moved = True

                        grt.ocp_artwork_type = data["related_type"]
                        try:
                          grt.save()
                        except:
                          raise ValidationError("The skill name already exists and they are unique")

                        if not grt.resource_type:
                          #pass #raise ValidationError("There's no resource type! create it?")
                          new_rt = EconomicResourceType(
                            name=data["name"],
                            description=data["description"],
                            unit=out,
                            price_per_unit=data["price_per_unit"],
                            substitutable=False, #data["substitutable"],
                            context_agent=data["context_agent"],
                            url=data["url"],
                            photo_url=data["photo_url"],
                            created_by=request.user,
                            behavior="work",
                            inventory_rule="never",
                          )
                          new_rt.save()
                          grt.resource_type = new_rt
                          grt.save()

                          # mptt: get_ancestors(ascending=False, include_self=False)
                          ancs = parent_rt.get_ancestors(True, True)
                          for an in ancs:
                            #if an.clas != 'Artwork':
                              an = Ocp_Skill_Type.objects.get(id=an.id)
                              if an.resource_type:
                                for fv in an.resource_type.facets.all():
                                  new_rtfv = ResourceTypeFacetValue(
                                    resource_type=new_rt,
                                    facet_value=fv.facet_value
                                  )
                                  new_rtfv.save()
                                break
                              elif an.facet_value:
                                new_rtfv = ResourceTypeFacetValue(
                                    resource_type=new_rt,
                                    facet_value=an.facet_value
                                )
                                new_rtfv.save()
                                break

                        else:
                          rt = grt.resource_type;
                          rt.name = data["name"]
                          rt.description = data["description"]
                          rt.unit = out
                          rt.price_per_unit = data["price_per_unit"]
                          rt.substitutable = False #data["substitutable"]
                          rt.context_agent = data["context_agent"]
                          rt.url = data["url"]
                          rt.photo_url = data["photo_url"]
                          #rt.parent = data["parent"]
                          rt.edited_by = request.user
                          if moved:
                            old_rtfvs = ResourceTypeFacetValue.objects.filter(resource_type=rt)
                            for rtfv in old_rtfvs:
                              rtfv.delete()
                            # mptt: get_ancestors(ascending=False, include_self=False)
                            ancs = parent_st.get_ancestors(True, True)
                            for an in ancs:
                              #if an.clas != 'Artwork':
                                an = Ocp_Skill_Type.objects.get(id=an.id)
                                if an.resource_type:
                                  for fv in an.resource_type.facets.all():
                                    new_rtfv = ResourceTypeFacetValue(
                                      resource_type=rt,
                                      facet_value=fv.facet_value
                                    )
                                    new_rtfv.save()
                                  break
                                elif an.facet_value:
                                  new_rtfv = ResourceTypeFacetValue(
                                      resource_type=rt,
                                      facet_value=an.facet_value
                                  )
                                  new_rtfv.save()
                                  break
                          rt.save()

                        nav_form = ExchangeNavForm(agent=agent, data=None)
                        Rtype_form = NewResourceTypeForm(agent=agent, data=None)
                        Stype_form = NewSkillTypeForm(agent=agent, data=None)

                      else: # is not Sid
                        pass
                  else: # have no parent_type id
                    pass
                else: # have no parent resource field
                  pass


        edit_exchange_type = request.POST.get("edit_exchange_type") # TODO the detail about transfertypes
        if edit_exchange_type:
            if ext_form.is_valid():
                data = ext_form.cleaned_data
                etid = data["edid"].split('_')[1]
                gen_ext = Ocp_Record_Type.objects.get(id=etid)
                new_parent = Ocp_Record_Type.objects.get(id=data["parent_type"].id)

                ext = gen_ext.exchange_type
                if ext:
                  ext.name = data["name"]
                  ext.context_agent = data['context_agent']
                else:
                  raise ValidationError("Editing Exchange Type! Without internal exchange_type TODO: "+gen_ext.name)
                gen_ext.name = data["name"]
                gen_ext.ocp_artwork_type = data['resource_type']
                gen_ext.ocp_skill_type = data['skill_type']
                moved = False
                if not gen_ext.parent.id == new_parent.id:
                  moved = True
                  raise ValidationError("Editing Exchange Type! Changed Parent TODO: "+data['parent_type'].name+' ext:'+str(new_parent)+' moved:'+str(moved))
                else:
                  gen_ext.save()
                  if ext:
                    ext.save()

                nav_form = ExchangeNavForm(agent=agent, data=None)
                Rtype_form = NewResourceTypeForm(agent=agent, data=None)
                Stype_form = NewSkillTypeForm(agent=agent, data=None)
                #raise ValidationError("Editing Exchange Type! "+data['parent_type'].name+' ext:'+str(new_parent)+' moved:'+str(moved))
                #uca = data["use_case"]
                #return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                #    % ('work/agent', agent.id, 'new-exchange-type', uca.id, 0)) # TODO page to add exchange type

        dt_selection_form = DateSelectionForm(data=request.POST)
        if dt_selection_form.is_valid():
            start = dt_selection_form.cleaned_data["start_date"]
            end = dt_selection_form.cleaned_data["end_date"]
            exchanges = Exchange.objects.exchanges_by_date_and_context(start, end, agent)
        else:
            exchanges = Exchange.objects.filter(context_agent=agent)

        if "categories" in request.POST:
            selected_values = request.POST["categories"]
            if selected_values:
                sv = selected_values.split(",")
                vals = []
                for v in sv:
                    vals.append(v.strip())
                if vals[0] == "all":
                    select_all = True
                else:
                    select_all = False
                    #transfers_included = []
                    exchanges_included = []
                    #events_included = []
                    for ex in exchanges:
                        if str(ex.exchange_type.id) in vals:
                            exchanges_included.append(ex)
                    exchanges = exchanges_included

                nav_form = ExchangeNavForm(agent=agent, data=None)
                Rtype_form = NewResourceTypeForm(agent=agent, data=None)
                Stype_form = NewSkillTypeForm(agent=agent, data=None)
        else:
          exchanges = Exchange.objects.filter(context_agent=agent) #.none()
          selected_values = "all"
    else:
        exchanges = Exchange.objects.exchanges_by_date_and_context(start, end, agent)

    exchanges_by_type = Exchange.objects.exchanges_by_type(agent)

    total_transfers = [{'unit':u,'name':'','clas':'','income':0,'incommit':0,'outgo':0,'outcommit':0, 'balance':0,'balnote':'','debug':''} for u in agent.used_units_ids()]
    total_rec_transfers = 0
    comma = ""

    fairunit = None
    #import pdb; pdb.set_trace()
    for x in exchanges:
        #try:
        #    xx = list(x.transfer_list)
        #except AttributeError:
        x.transfer_list = list(x.transfers.all())

        for transfer in x.transfer_list:
            if transfer.quantity():
              if transfer.transfer_type.is_incoming(x, agent): #reciprocal:
                sign = '<'
              else:
                sign = '>'
              uq = transfer.unit_of_quantity()
              rt = transfer.resource_type()
              if not uq and rt:
                uq = rt.unit
              if uq:
                if not hasattr(uq, 'ocp_unit_type'):
                  raise ValidationError("The unit has not ocp_unit_type! "+str(uq))
                for to in total_transfers:
                  if to['unit'] == uq.ocp_unit_type.id:

                    to['name'] = uq.ocp_unit_type.name
                    to['clas'] = uq.ocp_unit_type.clas

                    if transfer.transfer_type.is_incoming(x, agent): #is_reciprocal:
                      if transfer.events.all():
                        to['income'] = (to['income']*1) + (transfer.quantity()*1)
                      else:
                        to['incommit'] = (to['incommit']*1) + (transfer.quantity()*1)
                      #to['debug'] += str(x.id)+':'+str([ev.event_type.name+':'+str(ev.quantity)+':'+ev.resource_type.name+':'+ev.resource_type.ocp_artwork_type.name for ev in x.transfer_give_events()])+sign+' - '
                    else:
                      if transfer.events.all():
                        to['outgo'] = (to['outgo']*1) + (transfer.quantity()*1)
                      else:
                        to['outcommit'] = (to['outcommit']*1) + (transfer.quantity()*1)
                      #to['debug'] += str(x.id)+':'+str([str(ev.event_type.name)+':'+str(ev.quantity)+':'+ev.resource_type.name+':'+ev.resource_type.ocp_artwork_type.name for ev in x.transfer_receive_events()])+sign+' - '

                    if uq.ocp_unit_type.clas == 'each':
                      rt = transfer.resource_type()
                      rt.cur = False
                      if hasattr(rt, 'ocp_artwork_type') and rt.ocp_artwork_type:
                        ancs = rt.ocp_artwork_type.get_ancestors(False,True)
                        for an in ancs:
                          if an.clas == "currency":
                            rt.cur = True
                        if rt.cur:
                          to['debug'] += str(transfer.quantity())+'-'+str(rt.ocp_artwork_type.ocpArtworkType_unit_type.ocp_unit_type.name)+sign+' - '
                          for ttr in total_transfers:
                            if ttr['unit'] == rt.ocp_artwork_type.ocpArtworkType_unit_type.ocp_unit_type.id:
                              ttr['name'] = rt.ocp_artwork_type.ocpArtworkType_unit_type.ocp_unit_type.name
                              ttr['clas'] = rt.ocp_artwork_type.ocpArtworkType_unit_type.ocp_unit_type.clas

                              if transfer.events.all():
                                if sign == '<':
                                  ttr['income'] = (ttr['income']*1) + (transfer.quantity()*1)
                                if sign == '>':
                                  ttr['outgo'] = (ttr['outgo']*1) + (transfer.quantity()*1)
                                ttr['balance'] = (ttr['income']*1) - (ttr['outgo']*1)
                              else:
                                if sign == '<':
                                  ttr['incommit'] = (ttr['incommit']*1) + (transfer.quantity()*1)
                                if sign == '>':
                                  ttr['outcommit'] = (ttr['outcommit']*1) + (transfer.quantity()*1)
                              break
                      elif rt:
                        to['debug'] += '::'+str(rt)+'!!'+sign+'::'

                      #to['debug'] += str(x.transfer_give_events())+':'
                    elif uq.ocp_unit_type.clas == 'faircoin':

                      fairunit = uq.ocp_unit_type.id

                      to['balnote'] = (to['income']*1) - (to['outgo']*1)
                      #to['debug'] += str(x.transfer_give_events())+':'

                    elif uq.ocp_unit_type.clas == 'euro':
                      to['balance'] = (to['income']*1) - (to['outgo']*1)

                      to['debug'] += str([ev.event_type.name+':'+str(ev.quantity)+':'+ev.resource_type.name for ev in transfer.events.all()])+sign+' - '
                    else:
                      to['debug'] += 'U:'+str(uq.ocp_unit_type)+sign

              else: # not uq
                pass #total_transfers[1]['debug'] += ' :: '+str(transfer.name)+sign
            else: # not quantity
                pass

            for event in transfer.events.all():
                event_ids = event_ids + comma + str(event.id)
                comma = ","

        # end for transfer in x.transfer_list

        #import pdb; pdb.set_trace()
        for event in x.events.all():
            event_ids = event_ids + comma + str(event.id)
            comma = ","
        #todo: get sort to work

    # end for x in exchanges

    if fairunit:
        for to in total_transfers:
            if to['unit'] == fairunit:
                wal = agent.faircoin_resource()
                if wal:
                    if wal.is_wallet_address():
                        bal = wal.digital_currency_balance()
                        try:
                            to['balance'] = '{0:.4f}'.format(float(bal))
                        except ValueError:
                            to['balance'] = bal
                    else:
                        to['balance'] = '??'
                else:
                    to['balance'] = '!!'

    #import pdb; pdb.set_trace()

    return render(request, "work/exchanges_all.html", {
        "exchanges": exchanges,
        "exchanges_by_type": exchanges_by_type,
        "dt_selection_form": dt_selection_form,
        "total_transfers": total_transfers,
        "total_rec_transfers": total_rec_transfers,
        "select_all": select_all,
        "selected_values": selected_values,
        "ets": ets,
        "event_ids": event_ids,
        "context_agent": agent,
        "nav_form": nav_form,
        "usecases": usecases,
        "Etype_tree": exchange_types, #Ocp_Record_Type.objects.filter(lft__gt=gen_ext.lft, rght__lt=gen_ext.rght, tree_id=gen_ext.tree_id).exclude( Q(exchange_type__isnull=False), ~Q(exchange_type__context_agent__id__in=context_ids) ),
        "Rtype_tree": Ocp_Artwork_Type.objects.all().exclude( Q(resource_type__isnull=False), Q(resource_type__context_agent__isnull=False),  ~Q(resource_type__context_agent__id__in=context_ids) ),
        "Stype_tree": Ocp_Skill_Type.objects.all().exclude( Q(resource_type__isnull=False), Q(resource_type__context_agent__isnull=False), ~Q(resource_type__context_agent__id__in=context_ids) ),
        "Rtype_form": Rtype_form,
        "Stype_form": Stype_form,
        "Utype_tree": Ocp_Unit_Type.objects.filter(id__in=agent.used_units_ids()), #all(),
        #"unit_types": unit_types,
        "ext_form": ext_form,
    })


@login_required
def delete_exchange(request, exchange_id):
    #import pdb; pdb.set_trace()
    #todo: Lynn needs lots of work
    if request.method == "POST":
        exchange = get_object_or_404(Exchange, pk=exchange_id)
        if exchange.is_deletable:
            exchange.delete()
        next = request.POST.get("next")
        """if next == "exchanges":
            return HttpResponseRedirect('/%s/'
                % ('accounting/exchanges'))
        if next == "demand_transfers":
            return HttpResponseRedirect('/%s/'
                % ('accounting/sales-and-distributions')) #obsolete
        if next == "material_contributions":
            return HttpResponseRedirect('/%s/'
                % ('accounting/material-contributions')) #obsolete
        if next == "distributions":
            return HttpResponseRedirect('/%s/'
                % ('accounting/distributions'))"""
        if next == "exchanges-all":
            return HttpResponseRedirect('/%s/%s/%s/'
                % ('work/agent', exchange.context_agent.id, 'exchanges'))
       #todo: needs a fall-through if next is none of the above




#    E X C H A N G E   L O G G I N G

@login_required
def exchange_logging_work(request, context_agent_id, exchange_type_id=None, exchange_id=None):
    #import pdb; pdb.set_trace()
    context_agent = get_object_or_404(EconomicAgent, pk=context_agent_id)
    agent = get_agent(request)
    logger = False
    add_work_form = None
    if agent:
        if request.user.is_superuser:
            logger = True

    if exchange_type_id != "0": #new exchange
        if agent:
            exchange_type = get_object_or_404(ExchangeType, id=exchange_type_id)
            use_case = exchange_type.use_case

            exchange_form = ExchangeContextForm()
            #if request.method == "POST":
            #    exchange_form = ExchangeContextForm(data=request.POST)
            #    if exchange_form.is_valid():
            exchange = exchange_form.save(commit=False)
            exchange.context_agent = context_agent
            exchange.use_case = use_case
            exchange.exchange_type = exchange_type
            exchange.created_by = request.user
            exchange.start_date = datetime.date.today()
            exchange.save()

            return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                  % ('work/agent', context_agent.id, 'exchange-logging-work', 0, exchange.id))

            '''exchange_form = ExchangeContextForm()
            slots = exchange_type.slots()
            return render(request, "work/exchange_logging_work.html", {
                "use_case": use_case,
                "exchange_type": exchange_type,
                "exchange_form": exchange_form,
                "agent": agent,
                "context_agent": context_agent,
                "user": request.user,
                "logger": logger,
                "slots": slots,
                "total_t": 0,
                "total_rect": 0,
                "help": get_help("exchange"),
            })'''
        else:
            raise ValidationError("System Error: No agent, not allowed to create exchange.")

    elif exchange_id != "0": #existing exchange
        exchange = get_object_or_404(Exchange, id=exchange_id)

        if request.method == "POST":
            #import pdb; pdb.set_trace()
            exchange_form = ExchangeContextForm(instance=exchange, data=request.POST)
            if exchange_form.is_valid():
                exchange = exchange_form.save()
                return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
                    % ('work/agent', context_agent.id, 'exchange-logging-work', 0, exchange.id))

        exchange_type = exchange.exchange_type
        use_case = exchange_type.use_case
        exchange_form = ExchangeContextForm(instance=exchange)

        slots = []
        total_t = 0
        total_rect = 0
        #import pdb; pdb.set_trace()
        work_events = exchange.work_events()
        slots = exchange.slots_with_detail(context_agent)

        for slot in slots:
            if slot.is_incoming(exchange, context_agent) == True:
                #pass
                total_rect = total_rect + slot.total
                slot.is_income = True
            elif slot.is_incoming(exchange, context_agent) == False:
                total_t = total_t + slot.total
                slot.is_income = False
                #pass
            elif slot.is_reciprocal:
                total_rect = total_rect + slot.total
                slot.is_income = True
            else:
                total_t = total_t + slot.total
                slot.is_income = False

        if agent:
            #import pdb; pdb.set_trace()
            if request.user == exchange.created_by or context_agent in agent.managed_projects() or context_agent == agent:
                logger = True

            for event in work_events:
                event.changeform = WorkEventContextAgentForm(
                    context_agent=context_agent,
                    instance=event,
                    prefix=str(event.id))
            work_init = {
                "from_agent": agent,
                "event_date": datetime.date.today()
            }
            add_work_form = WorkEventContextAgentForm(initial=work_init, context_agent=context_agent)

            for slot in slots:
                ta_init = slot.default_to_agent
                fa_init = slot.default_from_agent
                if not ta_init:
                    ta_init = agent
                if not fa_init:
                    fa_init = agent
                xfer_init = {
                    "from_agent": fa_init,
                    "to_agent": ta_init,
                    "event_date": datetime.date.today()
                }
                slot.add_xfer_form = ContextTransferForm(initial=xfer_init, prefix="ATR" + str(slot.id), context_agent=context_agent, transfer_type=slot)
                slot.create_role_formset = resource_role_context_agent_formset(prefix=str(slot.id))
                ctx_qs = context_agent.related_all_agents_queryset()
                for form in slot.create_role_formset.forms:
                    form.fields["agent"].queryset = ctx_qs

                commit_init = {
                    "from_agent": fa_init,
                    "to_agent": ta_init,
                    "commitment_date": datetime.date.today(),
                    "due_date": exchange.start_date,
                }
                slot.add_commit_form = ContextTransferCommitmentForm(initial=commit_init, prefix="ACM" + str(slot.id), context_agent=context_agent, transfer_type=slot)

                slot.add_ext_agent = ContextExternalAgent() #initial=None, prefix="AGN"+str(slot.id))#, context_agent=context_agent)

            #import pdb; pdb.set_trace()
    else:
        raise ValidationError("System Error: No exchange or use case.")

    return render(request, "work/exchange_logging_work.html", {
        "use_case": use_case,
        "exchange": exchange,
        "exchange_type": exchange_type,
        "exchange_form": exchange_form,
        "agent": agent,
        "context_agent": context_agent,
        "logger": logger,
        "slots": slots,
        "work_events": work_events,
        "add_work_form": add_work_form,
        "total_t": total_t,
        "total_rect": total_rect,
        "help": get_help("exchange"),
        #"add_type": add_new_type_mkp(),
    })


def add_new_type_mkp(): # not used now
    out = "" #"<div class='add-new-type'><p>"
    out += str(_("If you don't find a type that suits, choose a subcategory and click:"))
    #out += "</p><a href='#' class='btn-mini'>New Resource Type</a>"
    #out += "</div>"
    return out


@login_required
def add_transfer_external_agent(request, commitment_id, context_agent_id):
    commitment = get_object_or_404(Commitment, pk=commitment_id)
    context_agent = get_object_or_404(EconomicAgent, pk=context_agent_id)
    exchange = commitment.exchange
    user_agent = get_agent(request)
    if not user_agent:
        return render(request, 'work/no_permission.html')
    if request.method == "POST":
        form = AgentCreateForm(request.POST)
        if form.is_valid():
            new_agent = form.save(commit=False)
            new_agent.created_by=request.user
            new_agent.save()
            if not commitment.to_agent and commitment.from_agent == context_agent:
                commitment.to_agent = new_agent
                commitment.save()
            elif not commitment.from_agent and commitment.to_agent == context_agent:
                commitment.from_agent = new_agent
                commitment.save()
            # TODO relate the context_agent


        #import pdb; pdb.set_trace()
    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', context_agent.id, 'exchange-logging-work', 0, exchange.id))



# functions copied from valuenetwork.views because were only running by staff

@login_required
def add_transfer(request, exchange_id, transfer_type_id):
    #import pdb; pdb.set_trace()
    exchange = get_object_or_404(Exchange, pk=exchange_id)
    transfer_type = get_object_or_404(TransferType, pk=transfer_type_id)
    if request.method == "POST":
        exchange_type = exchange.exchange_type
        context_agent = exchange.context_agent

        form = ContextTransferForm(data=request.POST, transfer_type=transfer_type, context_agent=context_agent, posting=True, prefix="ATR" + str(transfer_type.id))

        if form.is_valid():
            data = form.cleaned_data
            qty = data["quantity"]
            res = None
            res_from = None
            et2 = None
            res_identifier = None
            if qty:
                et_give = EventType.objects.get(name="Give")
                et_receive = EventType.objects.get(name="Receive")
                event_date = data["event_date"]
                if transfer_type.give_agent_is_context:
                    from_agent = context_agent
                else:
                    from_agent = data["from_agent"]
                if transfer_type.receive_agent_is_context:
                    to_agent = context_agent
                else:
                    to_agent = data["to_agent"]

                rt = data["resource_type"]
                if data["ocp_resource_type"]: #next and next == "exchange-work": # bumbum
                    gen_rt = data["ocp_resource_type"]
                    rt = get_rt_from_ocp_rt(gen_rt)

                #import pdb; pdb.set_trace()
                #if not transfer_type.can_create_resource:
                res = data["resource"]
                if transfer_type.is_currency:
                    res_from = data["from_resource"]
                description = data["description"]
                if transfer_type.is_currency:
                    value = qty
                    unit_of_value = rt.unit
                else:
                    value = data["value"]
                    if value:
                        unit_of_value = data["unit_of_value"]
                    else:
                        unit_of_value = None
                if transfer_type.is_contribution:
                    is_contribution = data["is_contribution"]
                else:
                    is_contribution = False
                if transfer_type.is_to_distribute:
                    is_to_distribute = data["is_to_distribute"]
                else:
                    is_to_distribute = False
                event_ref = data["event_reference"]
                if transfer_type.can_create_resource:
                    #res = data["resource"]
                    if not res:
                        res_identifier = data["identifier"]
                        if res_identifier:
                            res = EconomicResource(
                                identifier=res_identifier,
                                url=data["url"],
                                photo_url=data["photo_url"],
                                current_location=data["current_location"],
                                notes=data["notes"],
                                access_rules=data["access_rules"],
                                resource_type=rt,
                                exchange_stage=exchange_type,
                                quantity=0,
                                created_by=request.user,
                                )
                if exchange.exchange_type.use_case == UseCase.objects.get(identifier="supply_xfer"):
                    if transfer_type.is_reciprocal:
                        if res:
                            res.quantity -= qty
                        et = et_give
                    else:
                        if res:
                            res.quantity += qty
                        et = et_receive
                elif exchange.exchange_type.use_case == UseCase.objects.get(identifier="demand_xfer"):
                    if transfer_type.is_reciprocal:
                        if res:
                            res.quantity += qty
                        et = et_receive
                    else:
                        if res:
                            res.quantity -= qty
                        et = et_give
                else: #internal xfer use case
                    if transfer_type.is_reciprocal:
                        et = et_receive
                        et2 = et_give
                    else:
                        et = et_give
                        et2 = et_receive
                    if transfer_type.is_currency:
                        if res != res_from:
                            if res:
                                res.quantity += qty
                            if res_from:
                                res_from.quantity -= qty
                if res:
                    res.save()
                if res_from:
                    res_from.save()
                if res_identifier: #new resource
                    create_role_formset = resource_role_context_agent_formset(prefix=str(transfer_type.id), data=request.POST)
                    for form_rra in create_role_formset.forms:
                        if form_rra.is_valid():
                            data_rra = form_rra.cleaned_data
                            if data_rra:
                                data_rra = form_rra.cleaned_data
                                role = data_rra["role"]
                                agent = data_rra["agent"]
                                if role and agent:
                                    rra = AgentResourceRole()
                                    rra.agent = agent
                                    rra.role = role
                                    rra.resource = res
                                    rra.is_contact = data_rra["is_contact"]
                                    rra.save()

                xfer_name = transfer_type.name
                if transfer_type.is_reciprocal:
                    xfer_name = xfer_name + " from " + from_agent.nick
                else:
                    xfer_name = xfer_name + " of " + rt.name
                xfer = Transfer(
                    name=xfer_name,
                    transfer_type = transfer_type,
                    exchange = exchange,
                    context_agent = context_agent,
                    transfer_date = event_date,
                    notes = description,
                    created_by = request.user
                    )
                xfer.save()
                #import pdb; pdb.set_trace()
                e_is_to_distribute = is_to_distribute
                if et == et_give:
                    e_is_to_distribute = False
                e_is_contribution = is_contribution
                if et == et_receive and et2:
                    e_is_contribution = False
                if et == et_give and res_from:
                    event_res = res_from
                else:
                    event_res = res
                event = EconomicEvent(
                    event_type = et,
                    event_date=event_date,
                    resource_type=rt,
                    resource=event_res,
                    transfer=xfer,
                    exchange_stage=exchange.exchange_type,
                    context_agent = context_agent,
                    quantity=qty,
                    unit_of_quantity = rt.unit,
                    value=value,
                    unit_of_value=unit_of_value,
                    from_agent = from_agent,
                    to_agent = to_agent,
                    is_contribution = e_is_contribution,
                    is_to_distribute = e_is_to_distribute,
                    event_reference=event_ref,
                    created_by = request.user,
                    )
                event.save()
                if et2:
                    e2_is_to_distribute = is_to_distribute
                    if et2 == et_give:
                        e2_is_to_distribute = False
                    e2_is_contribution = is_contribution
                    if et2 == et_receive:
                        e2_is_contribution = False
                    if et2 == et_give and res_from:
                        event_res = res_from
                    else:
                        event_res = res
                    event2 = EconomicEvent(
                        event_type = et2,
                        event_date=event_date,
                        resource_type=rt,
                        resource=event_res,
                        transfer=xfer,
                        exchange_stage=exchange.exchange_type,
                        context_agent = context_agent,
                        quantity=qty,
                        unit_of_quantity = rt.unit,
                        value=value,
                        unit_of_value=unit_of_value,
                        from_agent = from_agent,
                        to_agent = to_agent,
                        is_contribution = e2_is_contribution,
                        is_to_distribute = e2_is_to_distribute,
                        event_reference=event_ref,
                        created_by = request.user,
                    )
                    event2.save()

    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', context_agent.id, 'exchange-logging-work', 0, exchange.id))



@login_required
def add_transfer_commitment_work(request, exchange_id, transfer_type_id):
    transfer_type = get_object_or_404(TransferType, pk=transfer_type_id)
    exchange = get_object_or_404(Exchange, pk=exchange_id)
    if request.method == "POST":
        exchange_type = exchange.exchange_type
        context_agent = exchange.context_agent
        form = ContextTransferCommitmentForm(data=request.POST, transfer_type=transfer_type, context_agent=context_agent, posting=True, prefix="ACM" + str(transfer_type.id))
        #import pdb; pdb.set_trace()
        if form.is_valid():
            data = form.cleaned_data
            qty = data["quantity"]
            et2 = None
            if qty:
                commitment_date = data["commitment_date"]
                due_date = data["due_date"]
                if transfer_type.give_agent_is_context:
                    from_agent = context_agent
                else:
                    from_agent = data["from_agent"]
                if transfer_type.receive_agent_is_context:
                    to_agent = context_agent
                else:
                    to_agent = data["to_agent"]

                rt = data["resource_type"]
                if data["ocp_resource_type"]: #next and next == "exchange-work": # bumbum
                    gen_rt = data["ocp_resource_type"]
                    rt = get_rt_from_ocp_rt(gen_rt)

                description = data["description"]
                if transfer_type.is_currency:
                    value = qty
                    unit_of_value = rt.unit
                else:
                    value = data["value"]
                    if value:
                        unit_of_value = data["unit_of_value"]
                    else:
                        unit_of_value = None

                xfer_name = transfer_type.name
                if transfer_type.is_reciprocal:
                    if from_agent:
                      xfer_name = xfer_name + " from " + from_agent.nick
                    else:
                      xfer_name = xfer_name + " from ?"
                else:
                    xfer_name = xfer_name + " of " + rt.name
                xfer = Transfer(
                    name=xfer_name,
                    transfer_type = transfer_type,
                    exchange = exchange,
                    context_agent = context_agent,
                    transfer_date = commitment_date,
                    created_by = request.user
                    )
                xfer.save()

                if exchange.exchange_type.use_case == UseCase.objects.get(identifier="supply_xfer"):
                    if not transfer_type.is_reciprocal:
                        et = EventType.objects.get(name="Give")
                    else:
                        et = EventType.objects.get(name="Receive")
                elif exchange.exchange_type.use_case == UseCase.objects.get(identifier="demand_xfer"):
                    if transfer_type.is_reciprocal:
                        et = EventType.objects.get(name="Receive")
                    else:
                        et = EventType.objects.get(name="Give")
                else: #internal xfer use case
                    if transfer_type.is_reciprocal:
                        et = EventType.objects.get(name="Receive")
                        et2 = EventType.objects.get(name="Give")
                    else:
                        et = EventType.objects.get(name="Give")
                        et2 = EventType.objects.get(name="Receive")
                commit = Commitment(
                    event_type = et,
                    commitment_date=commitment_date,
                    due_date=due_date,
                    resource_type=rt,
                    exchange = exchange,
                    transfer=xfer,
                    exchange_stage=exchange.exchange_type,
                    context_agent = context_agent,
                    quantity=qty,
                    unit_of_quantity = rt.unit,
                    value=value,
                    unit_of_value=unit_of_value,
                    from_agent = from_agent,
                    to_agent = to_agent,
                    description=description,
                    created_by = request.user,
                    )
                commit.save()
                if et2:
                    commit2 = Commitment(
                        event_type = et2,
                        commitment_date=commitment_date,
                        due_date=due_date,
                        resource_type=rt,
                        exchange = exchange,
                        transfer=xfer,
                        exchange_stage=exchange.exchange_type,
                        context_agent = context_agent,
                        quantity=qty,
                        unit_of_quantity = rt.unit,
                        value=value,
                        unit_of_value=unit_of_value,
                        from_agent = from_agent,
                        to_agent = to_agent,
                        created_by = request.user,
                    )
                    commit2.save()

        else:
          # form not valid
          pass
    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', context_agent.id, 'exchange-logging-work', 0, exchange.id))



@login_required
def change_transfer_commitments_work(request, transfer_id):
    transfer = get_object_or_404(Transfer, pk=transfer_id)
    if request.method == "POST":
        commits = transfer.commitments.all()
        transfer_type = transfer.transfer_type
        exchange = transfer.exchange
        context_agent = transfer.context_agent
        #import pdb; pdb.set_trace()
        form = ContextTransferCommitmentForm(data=request.POST, transfer_type=transfer_type, context_agent=context_agent, posting=True, prefix=transfer.form_prefix() + "C") # "ACM" + str(transfer_type.id) )
        #import pdb; pdb.set_trace()
        if form.is_valid():
            data = form.cleaned_data
            et_give = EventType.objects.get(name="Give")
            et_receive = EventType.objects.get(name="Receive")
            qty = data["quantity"]
            if qty:
                commitment_date = data["commitment_date"]
                due_date = data["due_date"]
                if transfer_type.give_agent_is_context:
                    from_agent = context_agent
                else:
                    from_agent = data["from_agent"]
                if transfer_type.receive_agent_is_context:
                    to_agent = context_agent
                else:
                    to_agent = data["to_agent"]

                rt = data["resource_type"]
                if data["ocp_resource_type"]: #next and next == "exchange-work": # bumbum
                    gen_rt = data["ocp_resource_type"]
                    rt = get_rt_from_ocp_rt(gen_rt)


                description = data["description"]
                if transfer_type.is_currency:
                    value = qty
                    unit_of_value = rt.unit
                else:
                    value = data["value"]
                    if value:
                        unit_of_value = data["unit_of_value"]
                    else:
                        unit_of_value = None

                for commit in commits:
                    commit.resource_type = rt
                    commit.from_agent = from_agent
                    commit.to_agent = to_agent
                    commit.commitment_date = commitment_date
                    commit.due_date = due_date
                    commit.quantity=qty
                    commit.unit_of_quantity = rt.unit
                    commit.value=value
                    commit.unit_of_value = unit_of_value
                    commit.description=description
                    commit.changed_by = request.user
                    commit.save()

    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', context_agent.id, 'exchange-logging-work', 0, exchange.id))



@login_required
def delete_transfer_commitments(request, transfer_id):
    transfer = get_object_or_404(Transfer, pk=transfer_id)
    exchange = transfer.exchange
    if request.method == "POST":
        for commit in transfer.commitments.all():
            if commit.is_deletable():
                commit.delete()
        if transfer.is_deletable():
             transfer.delete()
    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', transfer.context_agent.id, 'exchange-logging-work', 0, exchange.id))



@login_required
def transfer_from_commitment(request, transfer_id):
    transfer = get_object_or_404(Transfer, pk=transfer_id)
    transfer_type = transfer.transfer_type
    exchange = transfer.exchange
    context_agent = transfer.context_agent
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        form = ContextTransferForm(data=request.POST, transfer_type=transfer.transfer_type, context_agent=transfer.context_agent, posting=True, prefix=transfer.form_prefix())
        if form.is_valid():
            data = form.cleaned_data
            et_give = EventType.objects.get(name="Give")
            et_receive = EventType.objects.get(name="Receive")
            qty = data["quantity"]
            event_date = data["event_date"]
            if transfer_type.give_agent_is_context:
                from_agent = context_agent
            else:
                from_agent = data["from_agent"]
            if transfer_type.receive_agent_is_context:
                to_agent = context_agent
            else:
                to_agent = data["to_agent"]

            rt = data["resource_type"]
            if data["ocp_resource_type"]: #next and next == "exchange-work": # bumbum
                gen_rt = data["ocp_resource_type"]
                rt = get_rt_from_ocp_rt(gen_rt)

            #if not transfer_type.can_create_resource:
            res = data["resource"]
            description = data["description"]
            if transfer_type.is_currency:
                value = qty
                unit_of_value = rt.unit
                res_from = data["from_resource"]
            else:
                res_from = None
                value = data["value"]
                if value:
                    unit_of_value = data["unit_of_value"]
                else:
                    unit_of_value = None
            if transfer_type.is_contribution:
                is_contribution = data["is_contribution"]
            else:
                is_contribution = False
            event_ref = data["event_reference"]
            #res = None
            if transfer_type.can_create_resource:
                #res = data["resource"]
                if not res:
                    res_identifier = data["identifier"]
                    if res_identifier: #new resource
                        res = EconomicResource(
                            identifier=res_identifier,
                            url=data["url"],
                            photo_url=data["photo_url"],
                            current_location=data["current_location"],
                            notes=data["notes"],
                            access_rules=data["access_rules"],
                            resource_type=rt,
                            exchange_stage=exchange.exchange_type,
                            quantity=0,
                            created_by=request.user,
                            )
                        res.save()
                        create_role_formset = transfer.create_role_formset(data=request.POST)
                        for form_rra in create_role_formset.forms:
                            if form_rra.is_valid():
                                data_rra = form_rra.cleaned_data
                                if data_rra:
                                    role = data_rra["role"]
                                    agent = data_rra["agent"]
                                    if role and agent:
                                        rra = AgentResourceRole()
                                        rra.agent = agent
                                        rra.role = role
                                        rra.resource = res
                                        rra.is_contact = data_rra["is_contact"]
                                        rra.save()
            for commit in transfer.commitments.all():
                if commit.event_type == et_give and res_from:
                    event_res = res_from
                else:
                    event_res = res
                event = EconomicEvent(
                    event_type=commit.event_type,
                    resource_type = rt,
                    resource = event_res,
                    from_agent = from_agent,
                    to_agent = to_agent,
                    exchange_stage=transfer.exchange.exchange_type,
                    transfer=transfer,
                    commitment=commit,
                    context_agent = transfer.context_agent,
                    event_date = event_date,
                    quantity=qty,
                    unit_of_quantity = rt.unit,
                    value=value,
                    unit_of_value = unit_of_value,
                    description=description,
                    event_reference=event_ref,
                    created_by = request.user,
                )
                event.save()
                if event_res:
                    if event.event_type == et_give:
                        event_res.quantity -= event.quantity
                    else:
                        event_res.quantity += event.quantity
                    event_res.save()
                commit.finished = True
                commit.save()

    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', transfer.context_agent.id, 'exchange-logging-work', 0, exchange.id))



@login_required
def change_transfer_events(request, transfer_id, context_agent_id=None):
    transfer = get_object_or_404(Transfer, pk=transfer_id)
    if context_agent_id:
      context_agent = get_object_or_404(EconomicAgent, pk=context_agent_id)
    if request.method == "POST":
        events = transfer.events.all()
        transfer_type = transfer.transfer_type
        exchange = transfer.exchange
        events = transfer.events.all()
        if not context_agent:
          if transfer.context_agent:
            context_agent = transfer.context_agent
          elif exchange.context_agent:
            context_agent = exchange.context_agent
          elif events:
            if events[0].to_agent == request.user.agent.agent:
              context_agent = request.user.agent.agent
            elif events[0].from_agent == request.user.agent.agent:
              context_agent = request.user.agent.agent
            #else:
              #from_resource, to_resource = transfer.give_and_receive_resources()
              #if transfer_type.is_reciprocal:
              #  context_agent = events[0].to_agent
              #else:
              #  context_agent = events[0].from_agent
        #import pdb; pdb.set_trace()
        form = ContextTransferForm(data=request.POST, transfer_type=transfer_type, context_agent=context_agent, posting=True, prefix=transfer.form_prefix() + "E")
        if form.is_valid():
            data = form.cleaned_data
            et_give = EventType.objects.get(name="Give")
            et_receive = EventType.objects.get(name="Receive")
            qty = data["quantity"]
            if qty:
                event_date = data["event_date"]
                if transfer_type.give_agent_is_context:
                    from_agent = context_agent
                else:
                    from_agent = data["from_agent"]
                if transfer_type.receive_agent_is_context:
                    to_agent = context_agent
                else:
                    to_agent = data["to_agent"]

                rt = data["resource_type"]
                if data["ocp_resource_type"]: #next and next == "exchange-work": # bumbum
                    gen_rt = data["ocp_resource_type"]
                    rt = get_rt_from_ocp_rt(gen_rt)

                res = data["resource"]
                res_from = None
                if transfer_type.is_currency:
                    res_from = data["from_resource"]
                description = data["description"]
                if transfer_type.is_currency:
                    value = qty
                    unit_of_value = rt.unit
                else:
                    value = data["value"]
                    if value:
                        unit_of_value = data["unit_of_value"]
                    else:
                        unit_of_value = None
                if transfer_type.is_contribution:
                    is_contribution = data["is_contribution"]
                else:
                    is_contribution = False
                event_ref = data["event_reference"]

                #old_res = None
                old_qty = events[0].quantity
                old_res_from, old_res = transfer.give_and_receive_resources()
                #if events[0].resource:
                #    old_res = events[0].resource
                for event in events:
                    event.resource_type = rt
                    event.resource = res
                    if res_from and event.event_type == et_give:
                        event.resource = res_from
                    event.from_agent = from_agent
                    event.to_agent = to_agent
                    event.event_date = event_date
                    event.quantity=qty
                    event.unit_of_quantity = rt.unit
                    event.value=value
                    event.unit_of_value = unit_of_value
                    event.description=description
                    event.event_reference=event_ref
                    event.changed_by = request.user
                    event.save()
                    res_to_change = event.resource
                    if event.event_type == et_give:
                        if old_res_from:
                            old_res_to_change = old_res_from
                        else:
                            old_res_to_change = old_res
                    else:
                        old_res_to_change = old_res
                    if res_to_change:
                        if old_res_to_change:
                            if res_to_change == old_res_to_change:
                                if event.event_type == et_give:
                                    res_to_change.quantity = res_to_change.quantity + old_qty - qty
                                else:
                                    res_to_change.quantity = res_to_change.quantity - old_qty + qty
                                res_to_change.save()
                            else:
                                if event.event_type == et_give:
                                    res_to_change.quantity = res_to_change.quantity - qty
                                    old_res_to_change.quantity = old_res_to_change.quantity + qty
                                else:
                                    res_to_change.quantity = res_to_change.quantity + qty
                                    old_res_to_change.quantity = old_res_to_change.quantity - qty
                                res_to_change.save()
                                old_res_to_change.save()
                        else:
                            if event.event_type == et_give:
                                res_to_change.quantity = res_to_change.quantity - qty
                            else:
                                res_to_change.quantity = res_to_change.quantity + qty
                            res_to_change.save()
                    else:
                        if old_res_to_change:
                            if event.event_type == et_give:
                                old_res_to_change.quantity = old_res_to_change.quantity + qty
                            else:
                                old_res_to_change.quantity = old_res_to_change.quantity - qty
                            old_res_to_change.save()

                transfer.transfer_date = event_date
                transfer.save()

    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', context_agent.id, 'exchange-logging-work', 0, exchange.id))



@login_required
def delete_transfer_events(request, transfer_id):
    transfer = get_object_or_404(Transfer, pk=transfer_id)
    exchange = transfer.exchange
    if request.method == "POST":
        res = None
        events = transfer.events.all()
        et_give = EventType.objects.get(name="Give")
        give_res = None
        receive_res = None
        if events:
            for event in events:
                if event.event_type == et_give:
                    give_res = event.resource
                else:
                    receive_res = event.resource
                event.delete()
            if give_res != receive_res:
                if give_res:
                    give_res.quantity += event.quantity
                if receive_res:
                    receive_res.quantity -= event.quantity
            if give_res:
                if give_res.is_deletable():
                    give_res.delete()
                else:
                    give_res.save()
            if receive_res:
                if receive_res.is_deletable():
                    receive_res.delete()
                else:
                    receive_res.save()
        if transfer.is_deletable():
             transfer.delete()
    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', transfer.context_agent.id, 'exchange-logging-work', 0, exchange.id))



@login_required
def add_work_for_exchange(request, exchange_id):
    #import pdb; pdb.set_trace()
    exchange = get_object_or_404(Exchange, pk=exchange_id)
    context_agent = exchange.context_agent
    form = WorkEventContextAgentForm(context_agent=context_agent, data=request.POST)
    if form.is_valid():
        event = form.save(commit=False)
        rt = event.resource_type
        event.event_type = EventType.objects.get(name="Time Contribution")
        event.exchange = exchange
        event.context_agent = context_agent
        event.to_agent = context_agent
        event.unit_of_quantity = rt.unit
        event.created_by = request.user
        event.changed_by = request.user
        event.save()
    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', context_agent.id, 'exchange-logging-work', 0, exchange.id))



@login_required
def change_exchange_work_event(request, event_id):
    event = get_object_or_404(EconomicEvent, id=event_id)
    exchange = event.exchange
    context_agent=exchange.context_agent
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        form = WorkEventContextAgentForm(
            context_agent=context_agent,
            instance=event,
            data=request.POST,
            prefix=str(event.id))
        if form.is_valid():
            data = form.cleaned_data
            #import pdb; pdb.set_trace()
            form.save()

    return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
        % ('work/agent', context_agent.id, 'exchange-logging-work', 0, exchange.id))



@login_required
def delete_event(request, event_id):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        event = get_object_or_404(EconomicEvent, pk=event_id)
        agent = event.from_agent
        process = event.process
        exchange = event.exchange
        distribution = event.distribution
        resource = event.resource
        if resource:
            if event.consumes_resources():
                resource.quantity += event.quantity
            if event.creates_resources():
                resource.quantity -= event.quantity
            if event.changes_stage():
                tbcs = process.to_be_changed_requirements()
                if tbcs:
                    tbc = tbcs[0]
                    tbc_evts = tbc.fulfilling_events()
                    if tbc_evts:
                        tbc_evt = tbc_evts[0]
                        resource.quantity = tbc_evt.quantity
                        tbc_evt.delete()
                    resource.stage = tbc.stage
                else:
                    resource.revert_to_previous_stage()
            event.delete()
            if resource.is_deletable():
                resource.delete()
            else:
                resource.save()
        else:
            event.delete()

    next = request.POST.get("next")
    """if next == "process":
        return HttpResponseRedirect('/%s/%s/'
            % ('accounting/process', process.id))
    if next == "cleanup-processes":
        return HttpResponseRedirect('/%s/'
            % ('accounting/cleanup-processes'))
    if next == "exchange":
        return HttpResponseRedirect('/%s/%s/%s/'
            % ('accounting/exchange', 0, exchange.id))"""
    if next == "exchange-work":
        return HttpResponseRedirect('/%s/%s/%s/%s/%s/'
            % ('work/agent', event.context_agent.id, 'exchange-logging-work', 0, exchange.id))
    """if next == "distribution":
        return HttpResponseRedirect('/%s/%s/'
            % ('accounting/distribution', distribution.id))
    if next == "resource":
        resource_id = request.POST.get("resource_id")
        return HttpResponseRedirect('/%s/%s/'
            % ('accounting/resource', resource_id))
    elif next == "contributions":
        page = request.POST.get("page")

        if page:
            return HttpResponseRedirect('/%s/%s/?page=%s'
                % ('accounting/contributionhistory', agent.id, page))
        else:
            return HttpResponseRedirect('/%s/%s/'
                % ('accounting/contributionhistory', agent.id))
    elif next == "work-contributions":
        page = request.POST.get("page")

        if page:
            return HttpResponseRedirect('/%s/?page=%s'
                % ('work/my-history', page))
        else:
            return HttpResponseRedirect('/%s/'
                % ('work/my-history'))
    elif next == "work":
        return HttpResponseRedirect('/%s/%s/'
            % ('work/process-logging', process.id))"""




def resource_role_context_agent_formset(prefix, data=None):
    #import pdb; pdb.set_trace()
    RraFormSet = modelformset_factory(
        AgentResourceRole,
        form=ResourceRoleContextAgentForm,
        can_delete=True,
        extra=4,
        )
    formset = RraFormSet(prefix=prefix, queryset=AgentResourceRole.objects.none(), data=data)
    return formset


def json_ocp_resource_type_resources_with_locations(request, ocp_artwork_type_id):
    #import pdb; pdb.set_trace()
    rs = EconomicResource.objects.filter(resource_type__ocp_artwork_type__isnull=False, resource_type__ocp_artwork_type__id=ocp_artwork_type_id)
    #import pdb; pdb.set_trace()
    resources = []
    for r in rs:
        loc = ""
        if r.current_location:
            loc = r.current_location.name
        fields = {
            "pk": r.pk,
            "identifier": r.identifier,
            "location": loc,
        }
        resources.append({"fields": fields})
    data = simplejson.dumps(resources, ensure_ascii=False)
    return HttpResponse(data, content_type="text/json-comment-filtered")





#    P R O J E C T   R E S O U R C E S


def project_all_resources(request, agent_id):
    #import pdb; pdb.set_trace()
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    contexts = agent.related_all_contexts()
    contexts.append(agent)
    #context_ids = [c.id for c in contexts]
    #other_contexts = EconomicAgent.objects.all().exclude(id__in=context_ids)
    rts = list(set([arr.resource.resource_type for arr in agent.resource_relationships()]))
    rt_ids = [arr.resource.id for arr in agent.resource_relationships()]
    fcr = agent.faircoin_resource()
    if fcr:
      rt_ids.append(fcr.id)
      rts.append(fcr.resource_type)
    #rts = list(set([arr.resource.resource_type for arr in AgentResourceRole.objects.filter(agent=agent)])) #__in=contexts)]))
    #resources = EconomicResource.objects.select_related().filter(quantity__gt=0).order_by('resource_type')
    #rts = EconomicResourceType.objects.all().exclude(context_agent__in=other_contexts)
    for rt in rts:
      rt.items = []
      for r in rt.resources.filter(pk__in=rt_ids):
        #if r.agent_resource_roles.all()[0].agent == agent: #in contexts:
          rt.items.append(r)

    resource_types = []
    facets = Facet.objects.all()
    select_all = True
    selected_values = "all"
    fvs = []
    if request.method == "POST":
        selected_values = request.POST.get("categories", "all");
        if selected_values:
            vals = selected_values.split(",")
            if vals[0] == "all":
                select_all = True
                #resources = EconomicResource.objects.select_related().filter(quantity__gt=0).order_by('resource_type')
                for rt in rts:
                    if rt.onhand_qty()>0:
                        resource_types.append(rt)
                if fcr and not fcr.resource_type in resource_types:
                    resource_types.append(fcr.resource_type)
            else:
                select_all = False
                #resources = EconomicResource.objects.select_related().filter(quantity__gt=0, resource_type__category__name__in=vals).order_by('resource_type')

                for val in vals:
                    val_split = val.split("_")
                    tide = val_split[1]
                    otyp = None
                    try:
                        otyp = Ocp_Artwork_Type.objects.get(id=tide)
                    except:
                      try:
                          otyp = Ocp_Skill_Type.objects.get(id=tide)
                      except:
                          pass
                    if otyp:
                        if otyp.facet_value:
                           fvs.append(otyp.facet_value)
                        elif otyp.resource_type:
                           fv = otyp.resource_type.facets.all()[0].facet_value
                           fvs.append(fv)

                rts = select_resource_types(fvs)
                for rt in rts:
                    if rt.onhand_qty()>0:
                        rt.items = []
                        for r in rt.resources.filter(pk__in=rt_ids):
                            rt.items.append(r)
                        if rt.items:
                            resource_types.append(rt)
                #resource_types.sort(key=lambda rt: rt.label())
    else:
        for rt in rts:
            if rt.onhand_qty()>0:
                resource_types.append(rt)
                fvs.append(rt.facets.all()[0].facet_value) # add first facetvalue
        if fcr and not fcr.resource_type in resource_types:
            resource_types.append(fcr.resource_type)

    Rtype_form = NewResourceTypeForm(agent=agent, data=request.POST or None)

    return render(request, "work/project_resources.html", {
        #"resources": resources,
        "resource_types": resource_types,
        "facets": facets,
        "facetvalues": fvs,
        "select_all": select_all,
        "selected_values": selected_values,
        "photo_size": (128, 128),
        "help": get_help("inventory"),
        'agent': agent,
        'Rtype_tree': Ocp_Artwork_Type.objects.all(),
        'Rtype_form': Rtype_form,
        'Stype_tree': Ocp_Skill_Type.objects.all(),
    })


def new_resource_type(request, agent_id, Rtype):
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    user_agent = get_agent(request)
    if not (agent == user_agent or user_agent in agent.managers()):
        return render(request, 'work/no_permission.html')

    # process savings TODO

    return HttpResponseRedirect('/%s/%s/%s/'
        % ('work/agent', agent.id, 'resources'))



def project_resource(request, agent_id, resource_id):
    #import pdb; pdb.set_trace()
    resource = get_object_or_404(EconomicResource, id=resource_id)
    agent = get_object_or_404(EconomicAgent, id=agent_id)
    user_agent = get_agent(request)
    if not (agent == user_agent or user_agent in agent.managers()):
        return render(request, 'work/no_permission.html')

    RraFormSet = modelformset_factory(
        AgentResourceRole,
        form=ResourceRoleAgentForm,
        can_delete=True,
        extra=4,
        )
    role_formset = RraFormSet(
        prefix="role",
        queryset=resource.agent_resource_roles.all()
        )

    if not resource.is_digital_currency_resource():
        process_add_form = None
        order_form = None
        process = None
        pattern = None
        if resource.producing_events():
            process = resource.producing_events()[0].process
            pattern = None
            if process:
                pattern = process.process_pattern
        else:
            if agent:
                form_data = {'name': 'Create ' + resource.identifier, 'start_date': resource.created_date, 'end_date': resource.created_date}
                process_add_form = AddProcessFromResourceForm(form_data)
                if resource.resource_type.recipe_is_staged():
                    init={"start_date": datetime.date.today(),}
                    order_form = StartDateAndNameForm(initial=init)

    if request.method == "POST":
        #import pdb; pdb.set_trace()
        process_save = request.POST.get("process-save")
        if process_save:
            process_add_form = AddProcessFromResourceForm(data=request.POST)
            if process_add_form.is_valid():
                process = process_add_form.save(commit=False)
                process.started = process.start_date
                process.finished = True
                process.created_by = request.user
                process.save()
                event = EconomicEvent()
                event.context_agent = process.context_agent
                event.event_date = process.end_date
                event.event_type = process.process_pattern.event_type_for_resource_type("out", resource.resource_type)
                event.process = process
                event.resource_type = resource.resource_type
                event.quantity = resource.quantity
                event.unit_of_quantity = resource.unit_of_quantity()
                event.resource = resource
                event.to_agent = event.context_agent
                event.from_agent = event.context_agent
                event.created_by = request.user
                event.save()
                return HttpResponseRedirect('/%s/%s/'
                    % ('accounting/resource', resource.id))
    if resource.is_digital_currency_resource():
        send_coins_form = None
        is_owner=False
        limit = 0
        if agent:
            is_owner = agent.owns(resource)
            if is_owner:
                if resource.address_is_activated():
                    send_coins_form = SendFairCoinsForm()
                    from valuenetwork.valueaccounting.faircoin_utils import network_fee
                    limit = resource.spending_limit()
        return render(request, "work/faircoin_account.html", {
            "resource": resource,
            "photo_size": (128, 128),
            "role_formset": role_formset,
            "agent": agent,
            "is_owner": is_owner,
            "send_coins_form": send_coins_form,
            "limit": limit,
        })
    else:
        return render(request, "work/project_resource.html", {
            "resource": resource,
            "photo_size": (128, 128),
            "process_add_form": process_add_form,
            "order_form": order_form,
            "role_formset": role_formset,
            "agent": agent,
        })



from mptt.exceptions import InvalidMove
from mptt.forms import MoveNodeForm

def movenode(request, node_id): # still not used
    rtype = get_object_or_404(Artwork_Type, pk=node_id)
    if request.method == 'POST':
        form = MoveNodeForm(rtype, request.POST)
        if form.is_valid():
            try:
                rtype = form.save()
                return HttpResponseRedirect(rtype.get_absolute_url())
            except InvalidMove:
                pass
    else:
        form = MoveNodeForm(rtype)

    return render(request, 'work/project_resources.html', {
        'form': form,
        'rtype': rtype,
        'Rtype_tree': Ocp_Artwork_Type.objects.all(),
        #'agent': agent,
    })







#    S I M P L E   T A S K S

@login_required
def my_tasks(request):
    #import pdb; pdb.set_trace()
    my_work = []
    #my_skillz = []
    other_wip = []
    agent = get_agent(request)
    #if agent:
    context_ids = [c.id for c in agent.related_contexts()]
    my_work = Commitment.objects.unfinished().filter(
        event_type__relationship="work",
        from_agent=agent)
    #skill_ids = agent.resource_types.values_list('resource_type__id', flat=True)
    #my_skillz = Commitment.objects.unfinished().filter(
    #    from_agent=None,
    #    context_agent__id__in=context_ids,
    #    event_type__relationship="todo",
    #    resource_type__id__in=skill_ids)
    #other_unassigned = Commitment.objects.unfinished().filter(
    #    from_agent=None,
    #    context_agent__id__in=context_ids,
    #    event_type__relationship="work").exclude(resource_type__id__in=skill_ids)
    todos = Commitment.objects.unfinished().filter(
        from_agent=None,
        context_agent__id__in=context_ids,
        event_type__relationship="todo")
    #else:
    #    other_unassigned = Commitment.objects.unfinished().filter(
    #        from_agent=None,
    #        event_type__relationship="work")
    #import pdb; pdb.set_trace()
    my_todos = Commitment.objects.todos().filter(from_agent=agent)
    init = {"from_agent": agent,}
    patterns = PatternUseCase.objects.filter(use_case__identifier='todo')
    if patterns:
        pattern = patterns[0].pattern
        todo_form = WorkTodoForm(agent=agent, pattern=pattern, initial=init)
    else:
        todo_form = WorkTodoForm(agent=agent, initial=init)
    #work_now = settings.USE_WORK_NOW
    #import pdb; pdb.set_trace()
    return render(request, "work/my_tasks.html", {
        "agent": agent,
        "my_work": my_work,
        #"my_skillz": my_skillz,
        #"other_unassigned": other_unassigned,
        "my_todos": my_todos,
        "todo_form": todo_form,
        #"work_now": work_now,
        "help": get_help("proc_log"),
    })


@login_required
def take_new_tasks(request):
    #import pdb; pdb.set_trace()
    #task_bugs change
    # this method needs some serious house cleaning...
    # to do later, see github issue cited below
    #my_work = []
    my_skillz = []
    other_wip = []
    agent = get_agent(request)
    #if agent:
    context_ids = [c.id for c in agent.related_contexts()]
    #my_work = Commitment.objects.unfinished().filter(
    #    event_type__relationship="todo",
    #    from_agent=agent)
    skill_ids = agent.resource_types.values_list('resource_type__id', flat=True)
    my_skillz = Commitment.objects.unfinished().filter(
        from_agent=None,
        context_agent__id__in=context_ids,
        #task_bugs change
        #event_type__relationship="work",
        event_type__relationship="todo",
        resource_type__id__in=skill_ids)
    #other_unassigned = Commitment.objects.unfinished().filter(
    #    from_agent=None,
    #    context_agent__id__in=context_ids,
    #    event_type__relationship="work").exclude(resource_type__id__in=skill_ids)
    todos = Commitment.objects.unfinished().filter(
        from_agent=None,
        context_agent__id__in=context_ids,
        event_type__relationship="todo")
    #else:
    #    other_unassigned = Commitment.objects.unfinished().filter(
    #        from_agent=None,
    #        event_type__relationship="work")
    #import pdb; pdb.set_trace()
    my_todos = Commitment.objects.todos().filter(from_agent=agent)
    init = {"from_agent": agent,}
    patterns = PatternUseCase.objects.filter(use_case__identifier='todo')
    if patterns:
        pattern = patterns[0].pattern
        todo_form = WorkTodoForm(agent=agent, pattern=pattern, initial=init)
    else:
        todo_form = WorkTodoForm(agent=agent, initial=init)
    #work_now = settings.USE_WORK_NOW
    #task_bugs change
    # see https://github.com/FreedomCoop/valuenetwork/issues/263
    # process_tasks shd be filled
    process_tasks = []
    return render(request, "work/take_new_tasks.html", {
        "agent": agent,
        #"my_work": my_work,
        "process_tasks": process_tasks,
        "my_skillz": my_skillz,
        #"other_unassigned": other_unassigned,
        #"my_todos": my_todos,
        #"todo_form": todo_form,
        #"work_now": work_now,
        "help": get_help("proc_log"),
    })


@login_required
def add_todo(request):
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        patterns = PatternUseCase.objects.filter(use_case__identifier='todo')
        if patterns:
            pattern = patterns[0].pattern
            form = TodoForm(data=request.POST, pattern=pattern)
        else:
            form = TodoForm(request.POST)
        next = request.POST.get("next")
        agent = get_agent(request)
        et = None
        ets = EventType.objects.filter(
            relationship='todo')
        if ets:
            et = ets[0]
        if et:
            if form.is_valid():
                data = form.cleaned_data
                todo = form.save(commit=False)
                todo.to_agent=agent
                todo.event_type=et
                todo.quantity = Decimal("0")
                todo.unit_of_quantity=todo.resource_type.unit
                todo.save()
                if notification:
                    if todo.from_agent:
                        if todo.from_agent != agent:
                            site_name = get_site_name()
                            user = todo.from_agent.user()
                            if user:
                                #import pdb; pdb.set_trace()
                                notification.send(
                                    [user.user,],
                                    "valnet_new_todo",
                                    {"description": todo.description,
                                    "creator": agent,
                                    "site_name": site_name,
                                    }
                                )

    return HttpResponseRedirect(next)




#    P R O C E S S   T A S K S

@login_required
def project_work(request):
    #import pdb; pdb.set_trace()
    agent = get_agent(request)
    #task_bugs change
    projects = agent.related_contexts() #managed_projects()
    if not agent or agent.is_participant_candidate():
        return render(request, 'work/no_permission.html')
    next = "/work/project-work/"
    context_id = 0
    start = datetime.date.today() - datetime.timedelta(days=30)
    end = datetime.date.today() + datetime.timedelta(days=90)
    init = {"start_date": start, "end_date": end}
    date_form = DateSelectionForm(initial=init, data=request.POST or None)
    ca_form = WorkProjectSelectionFormOptional(data=request.POST or None, context_agents=projects)
    chosen_context_agent = None
    patterns = PatternUseCase.objects.filter(use_case__identifier='todo')
    if patterns:
        pattern = patterns[0].pattern
        todo_form = WorkTodoForm(pattern=pattern, agent=agent)
    else:
        todo_form = WorkTodoForm(agent=agent)
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        if date_form.is_valid():
            dates = date_form.cleaned_data
            start = dates["start_date"]
            end = dates["end_date"]
            if ca_form.is_valid():
                proj_data = ca_form.cleaned_data
                proj_id = proj_data["context_agent"]
                if proj_id.isdigit:
                    context_id = proj_id
                    chosen_context_agent = EconomicAgent.objects.get(id=proj_id)

    start_date = start.strftime('%Y_%m_%d')
    end_date = end.strftime('%Y_%m_%d')
    processes, context_agents = assemble_schedule(start, end, chosen_context_agent)

    todos = Commitment.objects.todos().filter(due_date__range=(start, end))
    if chosen_context_agent:
        todos = todos.filter(context_agent=chosen_context_agent)
    my_project_todos = []
    for todo in todos:
        if todo.context_agent in projects:
            my_project_todos.append(todo)
    #import pdb; pdb.set_trace()
    return render(request, "work/project_work.html", {
        "agent": agent,
        "context_agents": context_agents,
        "all_processes": projects,
        "date_form": date_form,
        "start_date": start_date,
        "end_date": end_date,
        "context_id": context_id,
        "todo_form": todo_form,
        "ca_form": ca_form,
        "todos": my_project_todos,
        "next": next,
        "help": get_help("project_work"),
    })


@login_required
def work_change_process_sked_ajax(request):
    #import pdb; pdb.set_trace()
    proc_id = request.POST["proc_id"]
    process = Process.objects.get(id=proc_id)
    form = ScheduleProcessForm(prefix=proc_id,instance=process,data=request.POST)
    if form.is_valid():
        data = form.cleaned_data
        process.start_date = data["start_date"]
        process.end_date = data["end_date"]
        process.notes = data["notes"]
        process.save()
        return_data = "OK"
        return HttpResponse(return_data, content_type="text/plain")
    else:
        return HttpResponse(form.errors, content_type="text/json-comment-filtered")

@login_required
def work_change_process(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        form = ProcessForm(
            instance=process,
            data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            form.save()
            #next = request.POST.get("next")
            #if next:
            #    return HttpResponseRedirect('/%s/%s/'
            #        % ('work/process-logging', process.id))

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

@login_required
def process_logging(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    pattern = process.process_pattern
    context_agent = process.context_agent
    #import pdb; pdb.set_trace()
    agent = get_agent(request)
    user = request.user
    agent_projects = agent.related_contexts()
    if process.context_agent not in agent_projects:
        return render(request, 'valueaccounting/no_permission.html')
    logger = False
    worker = False
    super_logger = False
    todays_date = datetime.date.today()
    change_process_form = ProcessForm(instance=process)
    add_output_form = None
    add_citation_form = None
    add_consumable_form = None
    add_usable_form = None
    add_work_form = None
    unplanned_work_form = None
    unplanned_cite_form = None
    unplanned_consumption_form = None
    unplanned_use_form = None
    unplanned_output_form = None
    process_expense_form = None
    role_formset = None
    slots = []
    event_types = []
    work_now = settings.USE_WORK_NOW
    to_be_changed_requirement = None
    changeable_requirement = None

    work_reqs = process.work_requirements()
    consume_reqs = process.consumed_input_requirements()
    use_reqs = process.used_input_requirements()
    unplanned_work = process.uncommitted_work_events()

    if agent and pattern:
        slots = pattern.slots()
        event_types = pattern.event_types()
        #if request.user.is_superuser or request.user == process.created_by:
        if request.user.is_staff or request.user == process.created_by:
            logger = True
            super_logger = True
        #import pdb; pdb.set_trace()
        for req in work_reqs:
            req.changeform = req.change_work_form()
            if agent == req.from_agent:
                logger = True
                worker = True
            init = {"from_agent": agent,
                "event_date": todays_date,
                "is_contribution": True,}
            req.input_work_form_init = req.input_event_form_init(init=init)
        for req in consume_reqs:
            req.changeform = req.change_form()
        for req in use_reqs:
            req.changeform = req.change_form()
        for event in unplanned_work:
            event.changeform = UnplannedWorkEventForm(
                pattern=pattern,
                context_agent=context_agent,
                instance=event,
                prefix=str(event.id))
        output_resource_types = pattern.output_resource_types()
        unplanned_output_form = UnplannedOutputForm(prefix='unplannedoutput')
        unplanned_output_form.fields["resource_type"].queryset = output_resource_types
        role_formset = resource_role_context_agent_formset(prefix="resource")
        produce_et = EventType.objects.get(name="Resource Production")
        change_et = EventType.objects.get(name="Change")
        #import pdb; pdb.set_trace()
        if "out" in slots:
            if logger:
                if change_et in event_types:
                    to_be_changed_requirement = process.to_be_changed_requirements()
                    if to_be_changed_requirement:
                        to_be_changed_requirement = to_be_changed_requirement[0]
                    changeable_requirement = process.changeable_requirements()
                    if changeable_requirement:
                        changeable_requirement = changeable_requirement[0]
                else:
                    add_output_form = ProcessOutputForm(prefix='output')
                    add_output_form.fields["resource_type"].queryset = output_resource_types
        #import pdb; pdb.set_trace()
        if "work" in slots:
            if agent:
                work_init = {
                    "from_agent": agent,
                    "is_contribution": True,
                }
                work_resource_types = pattern.work_resource_types()
                if work_resource_types:
                    work_unit = work_resource_types[0].unit
                    #work_init = {"unit_of_quantity": work_unit,}
                    work_init = {
                        "from_agent": agent,
                        "unit_of_quantity": work_unit,
                        "is_contribution": True,
                    }
                    unplanned_work_form = UnplannedWorkEventForm(prefix="unplanned", context_agent=context_agent, initial=work_init)
                    unplanned_work_form.fields["resource_type"].queryset = work_resource_types
                    #if logger:
                    #    add_work_form = WorkCommitmentForm(initial=work_init, prefix='work', pattern=pattern)
                else:
                    unplanned_work_form = UnplannedWorkEventForm(prefix="unplanned", pattern=pattern, context_agent=context_agent, initial=work_init)
                    #is this correct? see commented-out lines above
                if logger:
                    date_init = {"due_date": process.end_date,}
                    add_work_form = WorkCommitmentForm(prefix='work', pattern=pattern, initial=date_init)

        if "cite" in slots:
            cite_unit = None
            if context_agent.unit_of_claim_value:
                cite_unit = context_agent.unit_of_claim_value
            unplanned_cite_form = UnplannedCiteEventForm(prefix='unplannedcite', pattern=pattern, cite_unit=cite_unit)
            if logger:
                add_citation_form = ProcessCitationForm(prefix='citation', pattern=pattern)
        if "consume" in slots:
            unplanned_consumption_form = UnplannedInputEventForm(prefix='unplannedconsumption', pattern=pattern)
            if logger:
                add_consumable_form = ProcessConsumableForm(prefix='consumable', pattern=pattern)
        if "use" in slots:
            unplanned_use_form = UnplannedInputEventForm(prefix='unplannedusable', pattern=pattern)
            if logger:
                add_usable_form = ProcessUsableForm(prefix='usable', pattern=pattern)
        if "payexpense" in slots:
            process_expense_form = ProcessExpenseEventForm(prefix='processexpense', pattern=pattern)

    cited_ids = [c.resource.id for c in process.citations()]
    #import pdb; pdb.set_trace()
    citation_requirements = process.citation_requirements()
    for cr in citation_requirements:
        cr.resources = []
        for evt in cr.fulfilling_events():
            resource = evt.resource
            resource.event = evt
            cr.resources.append(resource)

    output_resource_ids = [e.resource.id for e in process.production_events() if e.resource]

    return render(request, "work/process_logging.html", {
        "process": process,
        "change_process_form": change_process_form,
        "cited_ids": cited_ids,
        "citation_requirements": citation_requirements,
        "output_resource_ids": output_resource_ids,
        "agent": agent,
        "user": user,
        "logger": logger,
        "worker": worker,
        "super_logger": super_logger,
        "add_output_form": add_output_form,
        "add_citation_form": add_citation_form,
        "add_consumable_form": add_consumable_form,
        "add_usable_form": add_usable_form,
        "add_work_form": add_work_form,
        "unplanned_work_form": unplanned_work_form,
        "unplanned_cite_form": unplanned_cite_form,
        "unplanned_consumption_form": unplanned_consumption_form,
        "unplanned_use_form": unplanned_use_form,
        "unplanned_output_form": unplanned_output_form,
        "role_formset": role_formset,
        "process_expense_form": process_expense_form,
        "slots": slots,
        "to_be_changed_requirement": to_be_changed_requirement,
        "changeable_requirement": changeable_requirement,
        "work_reqs": work_reqs,
        "consume_reqs": consume_reqs,
        "uncommitted_consumption": process.uncommitted_consumption_events(),
        "use_reqs": use_reqs,
        "uncommitted_use": process.uncommitted_use_events(),
        "uncommitted_process_expenses": process.uncommitted_process_expense_events(),
        "unplanned_work": unplanned_work,
        "work_now": work_now,
        "help": get_help("process_work"),
    })

@login_required
def work_log_resource_for_commitment(request, commitment_id):
    ct = get_object_or_404(Commitment, pk=commitment_id)
    form = ct.resource_create_form(data=request.POST)
    #import pdb; pdb.set_trace()
    if form.is_valid():
        resource_data = form.cleaned_data
        agent = get_agent(request)
        resource_type = ct.resource_type
        qty = resource_data["event_quantity"]
        event_type = ct.event_type
        resource = None
        if resource_type.inventory_rule == "yes":
            resource = form.save(commit=False)
            resource.quantity = qty
            resource.resource_type = resource_type
            resource.created_by=request.user
            if not ct.resource_type.substitutable:
                resource.independent_demand = ct.independent_demand
                resource.order_item = ct.order_item
            if event_type.applies_stage():
                resource.stage = ct.stage
            resource.save()
            event_date = resource_data["created_date"]
        else:
            event_date = resource_data["event_date"]
        from_agent = resource_data["from_agent"]
        default_agent = ct.process.default_agent()
        if not from_agent:
            from_agent = default_agent
        event = EconomicEvent(
            resource = resource,
            commitment = ct,
            event_date = event_date,
            event_type = event_type,
            from_agent = from_agent,
            to_agent = default_agent,
            resource_type = ct.resource_type,
            process = ct.process,
            context_agent = ct.process.context_agent,
            quantity = qty,
            unit_of_quantity = ct.unit_of_quantity,
            created_by = request.user,
            changed_by = request.user,
        )
        event.save()
        ct.process.set_started(event.event_date, request.user)

    next = request.POST.get("next")
    if next:
        if next == "work":
            return HttpResponseRedirect('/%s/%s/'
                % ('work/process-logging', ct.process.id))

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', ct.process.id))
        
@login_required
def work_invite_collaborator(request, commitment_id):
    commitment = get_object_or_404(Commitment, pk=commitment_id)
    process = commitment.process
    if request.method == "POST":
        if notification:
            agent = get_agent(request)
            users = commitment.possible_work_users()
            site_name = get_site_name()
            if users:
                notification.send(
                    users,
                    "valnet_help_wanted",
                    {"resource_type": commitment.resource_type,
                    "due_date": commitment.due_date,
                    "hours": commitment.quantity,
                    "unit": commitment.resource_type.unit,
                    "description": commitment.description or "",
                    "process": commitment.process,
                    "creator": agent,
                    "site_name": site_name,
                    }
                )

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))
        
@login_required
def work_change_commitment(request, commitment_id):
    ct = get_object_or_404(Commitment, id=commitment_id)
    process = ct.process
    if request.method == "POST":
        
        agent = get_agent(request)
        prefix = ct.form_prefix()
        #import pdb; pdb.set_trace()
        if ct.event_type.relationship=="work":
            form = WorkCommitmentForm(instance=ct, data=request.POST, prefix=prefix)
        else:
            form = ChangeCommitmentForm(instance=ct, data=request.POST, prefix=prefix)
        next = request.POST.get("next")

        if form.is_valid():
            data = form.cleaned_data
            rt = ct.resource_type
            demand = ct.independent_demand
            new_qty = data["quantity"]
            
            #todo:
            #old_ct = Commitment.objects.get(id=commitment_id)
            #explode = handle_commitment_changes(old_ct, rt, new_qty, demand, demand)
            #flow todo: explode?
            #explode wd apply to rt changes, which will not happen here
            #handle_commitment_changes will propagate qty changes
            commitment = form.save()
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))  
        
@login_required
def work_add_to_resource_for_commitment(request, commitment_id):
    ct = get_object_or_404(Commitment, pk=commitment_id)
    form = ct.select_resource_form(data=request.POST)
    if form.is_valid():
        #import pdb; pdb.set_trace()
        data = form.cleaned_data
        agent = get_agent(request)
        resource = data["resource"]
        quantity = data["quantity"]
        if resource and quantity:
            resource.quantity += quantity
            resource.changed_by=request.user
            resource.save()
            event_type = ct.event_type
            default_agent = ct.process.default_agent()
            event = EconomicEvent(
                resource = resource,
                commitment = ct,
                event_date = datetime.date.today(),
                event_type = event_type,
                from_agent = default_agent,
                to_agent = default_agent,
                resource_type = ct.resource_type,
                process = ct.process,
                context_agent = ct.context_agent,
                quantity = quantity,
                unit_of_quantity = ct.unit_of_quantity,
                created_by = request.user,
                changed_by = request.user,
            )
            event.save()
            ct.process.set_started(event.event_date, request.user)


    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', ct.process.id))
        
from functools import partial, wraps

@login_required
def non_process_logging(request):
    member = get_agent(request)
    if not member:
        return HttpResponseRedirect('/%s/'
            % ('work/work-home'))

    TimeFormSet = modelformset_factory(
        EconomicEvent,
        form=WorkCasualTimeContributionForm,
        can_delete=False,
        extra=4,
        max_num=8,
        )

    init = []
    for i in range(0, 4):
        init.append({"is_contribution": False,})
    time_formset = TimeFormSet(
        queryset=EconomicEvent.objects.none(),
        initial = init,
        data=request.POST or None)
    #import pdb; pdb.set_trace()
    ctx_qs = member.related_context_queryset()
    for form in time_formset.forms:
        form.fields["context_agent"].queryset = ctx_qs
        #form.fields["context_agent"].empty_label = "choose...";
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        keep_going = request.POST.get("keep-going")
        just_save = request.POST.get("save")
        if time_formset.is_valid():
            events = time_formset.save(commit=False)
            pattern = None
            patterns = PatternUseCase.objects.filter(use_case__identifier='non_prod')
            if patterns:
                pattern = patterns[0].pattern
            else:
                raise ValidationError("no non-production ProcessPattern")
            if pattern:
                unit = Unit.objects.filter(
                    unit_type="time",
                    name__icontains="Hour")[0]
                for event in events:
                    if event.event_date and event.quantity:
                        event.from_agent=member
                        event.to_agent = event.context_agent.default_agent()
                        #event.is_contribution=True
                        rt = event.resource_type
                        event_type = pattern.event_type_for_resource_type("work", rt)
                        event.event_type=event_type
                        event.unit_of_quantity=unit
                        event.created_by=request.user
                        event.save()
            if keep_going:
                return HttpResponseRedirect('/%s/'
                    % ('work/non-process-logging'))
            else:
                return HttpResponseRedirect('/%s/'
                    % ('work/my-history'))

    return render(request, "work/non_process_logging.html", {
        "member": member,
        "time_formset": time_formset,
        "help": get_help("non_proc_log"),
    })



@login_required
def work_todo_done(request, todo_id):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        try:
            todo = Commitment.objects.get(id=todo_id)
        except Commitment.DoesNotExist:
            todo = None
        if todo:
            todo.finished = True
            todo.save()
            event = todo.todo_event()
            if not event:
                event = create_event_from_todo(todo)
                event.save()
    next = request.POST.get("next")
    return HttpResponseRedirect(next)

@login_required
def work_add_todo(request):
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        agent = get_agent(request)
        patterns = PatternUseCase.objects.filter(use_case__identifier='todo')
        if patterns:
            pattern = patterns[0].pattern
            form = WorkTodoForm(agent=agent, pattern=pattern, data=request.POST)
        else:
            form = WorkTodoForm(agent=agent, data=request.POST)
        next = request.POST.get("next")
        et = None
        ets = EventType.objects.filter(
            relationship='todo')
        if ets:
            et = ets[0]
        if et:
            if form.is_valid():
                data = form.cleaned_data
                todo = form.save(commit=False)
                todo.to_agent=agent
                todo.event_type=et
                todo.quantity = Decimal("0")
                todo.unit_of_quantity=todo.resource_type.unit
                todo.save()
                if notification:
                    if todo.from_agent:
                        if todo.from_agent != agent:
                            site_name = get_site_name()
                            user = todo.from_agent.user()
                            if user:
                                #import pdb; pdb.set_trace()
                                notification.send(
                                    [user.user,],
                                    "valnet_new_todo",
                                    {"description": todo.description,
                                    "creator": agent,
                                    "site_name": site_name,
                                    }
                                )

    return HttpResponseRedirect(next)

@login_required
def work_todo_delete(request, todo_id):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        try:
            todo = Commitment.objects.get(id=todo_id)
        except Commitment.DoesNotExist:
            todo = None
        if todo:
            if notification:
                if todo.from_agent:
                    agent = get_agent(request)
                    if todo.from_agent != agent:
                        site_name = get_site_name()
                        user = todo.from_agent.user()
                        if user:
                            #import pdb; pdb.set_trace()
                            notification.send(
                                [user.user,],
                                "valnet_deleted_todo",
                                {"description": todo.description,
                                "creator": agent,
                                "site_name": site_name,
                                }
                            )
            todo.delete()
    next = request.POST.get("next")
    return HttpResponseRedirect(next)

@login_required
def work_todo_change(request, todo_id):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        try:
            todo = Commitment.objects.get(id=todo_id)
        except Commitment.DoesNotExist:
            todo = None
        if todo:
            agent = get_agent(request)
            prefix = todo.form_prefix()
            patterns = PatternUseCase.objects.filter(use_case__identifier='todo')
            if patterns:
                pattern = patterns[0].pattern
                form = WorkTodoForm(data=request.POST, pattern=pattern, agent=agent, instance=todo, prefix=prefix)
            else:
                form = WorkTodoForm(data=request.POST, agent=agent, instance=todo, prefix=prefix)
            if form.is_valid():
                todo = form.save()

    next = request.POST.get("next")
    return HttpResponseRedirect(next)

@login_required
def work_todo_decline(request, todo_id):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        try:
            todo = Commitment.objects.get(id=todo_id)
        except Commitment.DoesNotExist:
            todo = None
        if todo:
            todo.from_agent=None
            todo.save()
    next = request.POST.get("next")
    return HttpResponseRedirect(next)

@login_required
def work_todo_time(request):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        todo_id = request.POST.get("todoId")
        try:
            todo = Commitment.objects.get(id=todo_id)
        except Commitment.DoesNotExist:
            todo = None
        if todo:
            hours = request.POST.get("hours")
            if hours:
                qty = Decimal(hours)
            else:
                qty = Decimal("0.0")
            #task_bugs change
            # was creating zero qty events
            event = todo.todo_event()
            if event:
                event.quantity = qty
                event.save()
            else:
                if qty:
                    event = create_event_from_todo(todo)
                    event.quantity = qty
                    event.save()
    return HttpResponse("Ok", content_type="text/plain")

@login_required
def work_todo_mine(request, todo_id):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        try:
            todo = Commitment.objects.get(id=todo_id)
        except Commitment.DoesNotExist:
            todo = None
        if todo:
            agent = get_agent(request)
            todo.from_agent = agent
            todo.save()
            #task_bugs change
            # was creating an event here
    next = request.POST.get("next")
    if next:
        return HttpResponseRedirect(next)
    return HttpResponseRedirect('/%s/'
        % ('work/my-dashboard'))

@login_required
def work_todo_description(request):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        todo_id = request.POST.get("todoId")
        try:
            todo = Commitment.objects.get(id=todo_id)
        except Commitment.DoesNotExist:
            todo = None
        if todo:
            did = request.POST.get("did")
            event = todo.todo_event()
            if event:
                event.description = did
                event.save()

    return HttpResponse("Ok", content_type="text/plain")

@login_required
def work_commit_to_task(request, commitment_id):
    ct = get_object_or_404(Commitment, id=commitment_id)
    process = ct.process
    if request.method == "POST":
        agent = get_agent(request)
        prefix = ct.form_prefix()
        form = CommitmentForm(data=request.POST, prefix=prefix)
        next = None
        next = request.POST.get("next")
        #import pdb; pdb.set_trace()
        if form.is_valid():
            data = form.cleaned_data
            #todo: next line did not work, don't want to take time to figure out why right now
            #probly form shd have ct as instance.
            #ct = form.save(commit=False)
            start_date = data["start_date"]
            description = data["description"]
            quantity = data["quantity"]
            unit_of_quantity = data["unit_of_quantity"]
            ct.start_date=start_date
            ct.quantity=quantity
            ct.unit_of_quantity=unit_of_quantity
            ct.description=description
            ct.from_agent = agent
            ct.changed_by=request.user
            ct.save()
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

@login_required
def work_uncommit(request, commitment_id):
    ct = get_object_or_404(Commitment, id=commitment_id)
    process = ct.process
    if request.method == "POST":
        ct.from_agent = None
        ct.save()

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

@login_required
def work_add_process_worker(request, process_id):
    process = get_object_or_404(Process, pk=process_id)
    if request.method == "POST":
        import pdb; pdb.set_trace()
        form = WorkCommitmentForm(data=request.POST, prefix='work')
        if form.is_valid():
            input_data = form.cleaned_data
            demand = process.independent_demand()
            rt = input_data["resource_type"]
            pattern = process.process_pattern
            event_type = pattern.event_type_for_resource_type("work", rt)
            ct = form.save(commit=False)
            ct.process=process
            #flow todo: test order_item
            ct.order_item = process.order_item()
            ct.independent_demand=demand
            ct.event_type=event_type
            #ct.due_date=process.end_date
            ct.resource_type=rt
            ct.context_agent=process.context_agent
            ct.unit_of_quantity=rt.directional_unit("use")
            ct.created_by=request.user
            ct.save()
            if notification:
                #import pdb; pdb.set_trace()
                agent = get_agent(request)
                users = ct.possible_work_users()
                site_name = get_site_name()
                if users:
                    notification.send(
                        users,
                        "valnet_help_wanted",
                        {"resource_type": ct.resource_type,
                        "due_date": ct.due_date,
                        "hours": ct.quantity,
                        "unit": ct.resource_type.unit,
                        "description": ct.description or "",
                        "process": ct.process,
                        "creator": agent,
                        "site_name": site_name,
                        }
                    )
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

@login_required
def work_delete_event(request, event_id):
    #import pdb; pdb.set_trace()
    event = get_object_or_404(EconomicEvent, pk=event_id)
    process = event.process
    if request.method == "POST":
        agent = event.from_agent
        exchange = event.exchange
        distribution = event.distribution
        resource = event.resource
        if resource:
            if event.consumes_resources():
                resource.quantity += event.quantity
            if event.creates_resources():
                resource.quantity -= event.quantity
            if event.changes_stage():
                tbcs = process.to_be_changed_requirements()
                if tbcs:
                    tbc = tbcs[0]
                    tbc_evts = tbc.fulfilling_events()
                    if tbc_evts:
                        tbc_evt = tbc_evts[0]
                        resource.quantity = tbc_evt.quantity
                        tbc_evt.delete()
                    resource.stage = tbc.stage
                else:
                    resource.revert_to_previous_stage()
            event.delete()
            if resource.is_deletable():
                resource.delete()
            else:
                resource.save()
        else:
            event.delete()

    next = request.POST.get("next")
    if next:
        if next != "process-logging":
            return HttpResponseRedirect(next)
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

@login_required
def work_add_work_event(request, commitment_id):
    ct = get_object_or_404(Commitment, pk=commitment_id)
    form = ct.input_event_form_init(data=request.POST)
    #import pdb; pdb.set_trace()
    if form.is_valid():
        event = form.save(commit=False)
        event.commitment = ct
        event.event_type = ct.event_type
        #event.from_agent = ct.from_agent
        event.to_agent = ct.process.default_agent()
        event.resource_type = ct.resource_type
        event.process = ct.process
        event.context_agent = ct.context_agent
        event.unit_of_quantity = ct.unit_of_quantity
        event.created_by = request.user
        event.changed_by = request.user
        event.save()
        ct.process.set_started(event.event_date, request.user)

    return HttpResponseRedirect('/%s/%s/'
            % ('work/process-logging', ct.process.id))
            
@login_required
def work_change_work_event(request, event_id):
    event = get_object_or_404(EconomicEvent, id=event_id)
    commitment = event.commitment
    process = event.process
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        form = event.work_event_change_form(data=request.POST)
        if form.is_valid():
            #import pdb; pdb.set_trace()
            data = form.cleaned_data
            form.save()
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))
        
@login_required
def work_add_process_input(request, process_id, slot):
    process = get_object_or_404(Process, pk=process_id)
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        pattern = process.process_pattern
        if slot == "c":
            form = ProcessConsumableForm(data=request.POST, pattern=pattern, prefix='consumable')
            rel = "consume"
        elif slot == "u":
            form = ProcessUsableForm(data=request.POST, pattern=pattern, prefix='usable')
            rel = "use"
        if form.is_valid():
            input_data = form.cleaned_data
            qty = input_data["quantity"]
            if qty:
                demand = process.independent_demand()
                ct = form.save(commit=False)
                rt = input_data["resource_type"]
                pattern = process.process_pattern
                event_type = pattern.event_type_for_resource_type(rel, rt)
                ct.event_type = event_type
                ct.process = process
                ct.context_agent=process.context_agent
                ct.order_item = process.order_item()
                ct.independent_demand = demand
                ct.due_date = process.start_date
                ct.created_by = request.user
                #todo: add stage and state as args?
                #todo pr: this shd probably use own_or_parent_recipes
                #ptrt, inheritance = ct.resource_type.main_producing_process_type_relationship()
                #if ptrt:
                #    ct.context_agent = ptrt.process_type.context_agent
                ct.save()
                #todo: this is used in process logging; shd it explode?
                #explode_dependent_demands(ct, request.user)
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))
        
def work_json_directional_unit(request, resource_type_id, direction):
    #import pdb; pdb.set_trace()
    ert = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    defaults = {
        "unit": ert.directional_unit(direction).id,
    }
    data = simplejson.dumps(defaults, ensure_ascii=False)
    return HttpResponse(data, content_type="text/json-comment-filtered")
    
@login_required
def work_delete_process_commitment(request, commitment_id):
    commitment = get_object_or_404(Commitment, pk=commitment_id)
    process = commitment.process
    #commitment.delete_dependants()
    commitment.delete()
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))
        
@login_required
def work_add_unplanned_work_event(request, process_id):
    process = get_object_or_404(Process, pk=process_id)
    pattern = process.process_pattern
    #import pdb; pdb.set_trace()
    if pattern:
        form = UnplannedWorkEventForm(prefix="unplanned", data=request.POST, pattern=pattern)
        if form.is_valid():
            event = form.save(commit=False)
            rt = event.resource_type
            event.event_type = pattern.event_type_for_resource_type("work", rt)
            event.process = process
            event.context_agent = process.context_agent
            default_agent = process.default_agent()
            event.to_agent = default_agent
            event.unit_of_quantity = rt.unit
            event.created_by = request.user
            event.changed_by = request.user
            event.save()
            process.set_started(event.event_date, request.user)

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

@login_required
def work_change_unplanned_work_event(request, event_id):
    event = get_object_or_404(EconomicEvent, id=event_id)
    process = event.process
    pattern = process.process_pattern
    if pattern:
        #import pdb; pdb.set_trace()
        if request.method == "POST":
            form = UnplannedWorkEventForm(
                pattern=pattern,
                instance=event,
                prefix=str(event.id),
                data=request.POST)
            if form.is_valid():
                data = form.cleaned_data
                form.save()

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

@login_required
def work_add_unplanned_output(request, process_id):
    process = get_object_or_404(Process, pk=process_id)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        form = UnplannedOutputForm(data=request.POST, prefix='unplannedoutput')
        if form.is_valid():
            output_data = form.cleaned_data
            qty = output_data["quantity"]
            if qty:
                event = form.save(commit=False)
                rt = output_data["resource_type"]
                identifier = output_data["identifier"]
                notes = output_data["notes"]
                url = output_data["url"]
                photo_url = output_data["photo_url"]
                access_rules = output_data["access_rules"]
                demand = None
                if not rt.substitutable:
                    demand = process.independent_demand()
                    #flow todo: add order_item ? [no]
                    #N/A I think, but see also
                    #add_process_output

                resource = EconomicResource(
                    resource_type=rt,
                    identifier=identifier,
                    independent_demand=demand,
                    notes=notes,
                    url=url,
                    photo_url=photo_url,
                    quantity=event.quantity,
                    access_rules=access_rules,
                    #unit_of_quantity=event.unit_of_quantity,
                    created_by=request.user,
                )
                resource.save()

                event.resource = resource
                pattern = process.process_pattern
                event_type = pattern.event_type_for_resource_type("out", rt)
                event.event_type = event_type
                event.process = process
                event.context_agent = process.context_agent
                default_agent = process.default_agent()
                event.from_agent = default_agent
                event.to_agent = default_agent
                event.event_date = datetime.date.today()
                event.created_by = request.user
                event.save()
                process.set_started(event.event_date, request.user)

                next = request.POST.get("next")
                if next and next == "exchange-work":
                  role_formset =  resource_role_context_agent_formset(prefix="resource", data=request.POST)
                else:
                  role_formset =  resource_role_agent_formset(prefix="resource", data=request.POST)

                for form_rra in role_formset.forms:
                    if form_rra.is_valid():
                        data_rra = form_rra.cleaned_data
                        if data_rra:
                            role = data_rra["role"]
                            agent = data_rra["agent"]
                            if role and agent:
                                rra = AgentResourceRole()
                                rra.agent = agent
                                rra.role = role
                                rra.resource = resource
                                rra.is_contact = data_rra["is_contact"]
                                rra.save()
                #todo: add exchange-work redirect?

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

@login_required
def work_add_unplanned_input_event(request, process_id, slot):
    process = get_object_or_404(Process, pk=process_id)
    pattern = process.process_pattern
    #import pdb; pdb.set_trace()
    if pattern:
        if slot == "c":
            prefix = "unplannedconsumption"
            et = "consume"
        else:
            prefix = "unplannedusable"
            et = "use"
        form = UnplannedInputEventForm(
            prefix=prefix,
            data=request.POST,
            pattern=pattern,
            load_resources=True)
        if form.is_valid():
            agent = get_agent(request)
            data = form.cleaned_data
            agent = get_agent(request)
            rt = data["resource_type"]
            r_id = data["resource"]
            qty = data["quantity"]
            event_date = data["event_date"]
            unit = rt.unit
            if et == "use":
                unit = rt.unit_for_use()
            resource = EconomicResource.objects.get(id=r_id)
            default_agent = process.default_agent()
            from_agent = resource.owner() or default_agent
            event_type = pattern.event_type_for_resource_type(et, rt)
            event = EconomicEvent(
                event_type=event_type,
                resource_type = rt,
                resource = resource,
                from_agent = from_agent,
                to_agent = default_agent,
                process = process,
                context_agent = process.context_agent,
                event_date = event_date,
                quantity=qty,
                unit_of_quantity = unit,
                created_by = request.user,
                changed_by = request.user,
            )
            event.save()
            if event_type.consumes_resources():
                resource.quantity -= event.quantity
                resource.changed_by=request.user
                resource.save()
            process.set_started(event.event_date, request.user)

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

def json_resource_type_resources(request, resource_type_id):
    #import pdb; pdb.set_trace()
    json = serializers.serialize("json", EconomicResource.objects.filter(resource_type=resource_type_id), fields=('identifier'))
    return HttpResponse(json, content_type='application/json')
    
@login_required
def work_add_consumption_event(request, commitment_id, resource_id):
    ct = get_object_or_404(Commitment, pk=commitment_id)
    process = ct.process
    resource = get_object_or_404(EconomicResource, pk=resource_id)
    prefix = resource.form_prefix()
    form = InputEventForm(prefix=prefix, data=request.POST)
    if form.is_valid():
        agent = get_agent(request)
        event = form.save(commit=False)
        event.commitment = ct
        event.event_type = ct.event_type
        event.resource_type = ct.resource_type
        event.resource = resource
        event.process = ct.process
        event.context_agent = ct.context_agent
        default_agent = ct.process.default_agent()
        event.from_agent = default_agent
        event.to_agent = default_agent
        event.unit_of_quantity = ct.unit_of_quantity
        event.created_by = request.user
        event.changed_by = request.user
        event.save()
        if ct.consumes_resources():
            resource.quantity -= event.quantity
            resource.changed_by=request.user
            resource.save()
        ct.process.set_started(event.event_date, request.user)

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))
        
@login_required
def work_add_use_event(request, commitment_id, resource_id):
    ct = get_object_or_404(Commitment, pk=commitment_id)
    resource = get_object_or_404(EconomicResource, pk=resource_id)
    prefix = resource.form_prefix()
    unit = ct.resource_type.directional_unit("use")
    qty_help = " ".join(["unit:", unit.abbrev])
    form = InputEventForm(qty_help=qty_help, prefix=prefix, data=request.POST)
    if form.is_valid():
        agent = get_agent(request)
        event = form.save(commit=False)
        event.commitment = ct
        event.event_type = ct.event_type
        event.from_agent = agent
        event.resource_type = ct.resource_type
        event.resource = resource
        event.process = ct.process
        #event.project = ct.project
        default_agent = ct.process.default_agent()
        event.from_agent = default_agent
        event.to_agent = default_agent
        event.context_agent = ct.context_agent
        event.unit_of_quantity = unit
        event.created_by = request.user
        event.changed_by = request.user
        event.save()
        ct.process.set_started(event.event_date, request.user)

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', ct.process.id))

@login_required
def work_add_process_output(request, process_id):
    process = get_object_or_404(Process, pk=process_id)
    if request.method == "POST":
        form = ProcessOutputForm(data=request.POST, prefix='output')
        if form.is_valid():
            output_data = form.cleaned_data
            qty = output_data["quantity"]
            if qty:
                ct = form.save(commit=False)
                rt = output_data["resource_type"]
                pattern = process.process_pattern
                event_type = pattern.event_type_for_resource_type("out", rt)
                ct.event_type = event_type
                ct.process = process
                ct.context_agent = process.context_agent
                ct.independent_demand = process.independent_demand()
                ct.due_date = process.end_date
                ct.created_by = request.user
                ct.save()
                if process.name == "Make something":
                    process.name = " ".join([
                                "Make",
                                ct.resource_type.name,
                            ])
                else:
                    process.name = " and ".join([
                                process.name,
                                ct.resource_type.name,
                            ])
                if len(process.name) > 128:
                    process.name = process.name[0:128]
                process.save()

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))

@login_required
def work_log_stage_change_event(request, commitment_id, resource_id):
    to_be_changed_commitment = get_object_or_404(Commitment, pk=commitment_id)
    process = to_be_changed_commitment.process
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        resource = get_object_or_404(EconomicResource, pk=resource_id)
        quantity = resource.quantity 
        default_agent = process.default_agent()
        from_agent = default_agent
        event_date = datetime.date.today()
        prefix = resource.form_prefix()
        #shameless hack
        qty_field = prefix + "-quantity"
        if request.POST.get(qty_field):
            form = resource.transform_form(data=request.POST)
            if form.is_valid():
                data = form.cleaned_data
                quantity = data["quantity"]
                event_date = data["event_date"]
                from_agent = data["from_agent"]
        change_commitment = process.changeable_requirements()[0]
        rt = to_be_changed_commitment.resource_type
        event = EconomicEvent(
            commitment=to_be_changed_commitment,
            event_type=to_be_changed_commitment.event_type,
            resource_type = rt,
            resource = resource,
            from_agent = from_agent,
            to_agent = default_agent,
            process = process,
            context_agent = process.context_agent,
            event_date = event_date,
            quantity=resource.quantity,
            unit_of_quantity = rt.unit,
            created_by = request.user,
            changed_by = request.user,
        )
        event.save()
        event = EconomicEvent(
            commitment=change_commitment,
            event_type=change_commitment.event_type,
            resource_type = rt,
            resource = resource,
            from_agent = from_agent,
            to_agent = default_agent,
            process = process,
            context_agent = process.context_agent,
            event_date = event_date,
            quantity=quantity,
            unit_of_quantity = rt.unit,
            created_by = request.user,
            changed_by = request.user,
        )
        event.save()
        resource.stage = change_commitment.stage
        resource.quantity = quantity
        resource.save()
        process.set_started(event.event_date, request.user)
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))        

@login_required
def work_add_process_citation(request, process_id):
    process = get_object_or_404(Process, pk=process_id)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        form = ProcessCitationForm(data=request.POST, prefix='citation')
        if form.is_valid():
            input_data = form.cleaned_data
            demand = process.independent_demand()
            quantity = Decimal("1")
            rt = input_data["resource_type"]
            descrip = input_data["description"]
            pattern = process.process_pattern
            event_type = pattern.event_type_for_resource_type("cite", rt)
            agent = get_agent(request)
            ct = Commitment(
                process=process,
                #from_agent=agent,
                independent_demand=demand,
                order_item = process.order_item(),
                event_type=event_type,
                due_date=process.start_date,
                resource_type=rt,
                context_agent=process.context_agent,
                quantity=quantity,
                description=descrip,
                unit_of_quantity=rt.directional_unit("cite"),
                created_by=request.user,
            )
            ct.save()

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))    
        
@login_required
def work_add_citation_event(request, commitment_id, resource_id):
    #import pdb; pdb.set_trace()
    ct = get_object_or_404(Commitment, pk=commitment_id)
    resource = get_object_or_404(EconomicResource, pk=resource_id)
    prefix = resource.form_prefix()
    unit = ct.resource_type.directional_unit("use")
    qty_help = " ".join(["unit:", unit.abbrev])
    form = InputEventForm(qty_help=qty_help, prefix=prefix, data=request.POST)
    if form.is_valid():
        agent = get_agent(request)
        event = form.save(commit=False)
        event.commitment = ct
        event.event_type = ct.event_type
        event.from_agent = agent
        event.resource_type = ct.resource_type
        event.resource = resource
        event.process = ct.process
        default_agent = ct.process.default_agent()
        event.from_agent = default_agent
        event.to_agent = default_agent
        event.context_agent = ct.context_agent
        event.unit_of_quantity = unit
        event.created_by = request.user
        event.changed_by = request.user
        event.save()
        ct.process.set_started(event.event_date, request.user)

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', ct.process.id))
        
@login_required
def work_add_unplanned_cite_event(request, process_id):
    process = get_object_or_404(Process, pk=process_id)
    pattern = process.process_pattern
    #import pdb; pdb.set_trace()
    if pattern:
        form = UnplannedCiteEventForm(
            prefix='unplannedcite',
            data=request.POST,
            pattern=pattern,
            load_resources=True)
        if form.is_valid():
            data = form.cleaned_data
            qty = data["quantity"]
            if qty:
                agent = get_agent(request)
                rt = data["resource_type"]
                r_id = data["resource"]
                resource = EconomicResource.objects.get(id=r_id)
                #todo: rethink for citations
                default_agent = process.default_agent()
                from_agent = resource.owner() or default_agent
                event_type = pattern.event_type_for_resource_type("cite", rt)
                event = EconomicEvent(
                    event_type=event_type,
                    resource_type = rt,
                    resource = resource,
                    from_agent = from_agent,
                    to_agent = default_agent,
                    process = process,
                    context_agent = process.context_agent,
                    event_date = datetime.date.today(),
                    quantity=qty,
                    unit_of_quantity = rt.directional_unit("cite"),
                    created_by = request.user,
                    changed_by = request.user,
                )
                event.save()
                process.set_started(event.event_date, request.user)

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))
        
@login_required
def work_delete_citation_event(request, commitment_id, resource_id):
    #import pdb; pdb.set_trace()
    ct = get_object_or_404(Commitment, pk=commitment_id)
    process = ct.process
    if request.method == "POST":
        resource = get_object_or_404(EconomicResource, pk=resource_id)
        events = ct.fulfillment_events.filter(resource=resource)
        for event in events:
            event.delete()
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))
            
def json_resource_type_citation_unit(request, resource_type_id):
    #import pdb; pdb.set_trace()
    ert = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    direction = "use"
    defaults = {
        "unit": ert.directional_unit(direction).name,
    }
    data = simplejson.dumps(defaults, ensure_ascii=False)
    return HttpResponse(data, content_type="text/json-comment-filtered")
    
@login_required
def work_join_task(request, commitment_id):
    if request.method == "POST":
        ct = get_object_or_404(Commitment, id=commitment_id)
        process = ct.process
        agent = get_agent(request)

        if notification:
            #import pdb; pdb.set_trace()
            workers = ct.workers()
            users = []
            for worker in workers:
                worker_users = [au.user for au in worker.users.all()]
                users.extend(worker_users)
            site_name = get_site_name()
            if users:
                notification.send(
                    users,
                    "valnet_join_task",
                    {"resource_type": ct.resource_type,
                    "due_date": ct.due_date,
                    "hours": ct.quantity,
                    "unit": ct.resource_type.unit,
                    "description": ct.description or "",
                    "process": process,
                    "creator": agent,
                    "site_name": site_name,
                    }
                )

    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process.id))
        

 #    H I S T O R Y

@login_required
def my_history(request): # tasks history
    #import pdb; pdb.set_trace()
    #agent = get_object_or_404(EconomicAgent, pk=agent_id)
    user_agent = get_agent(request)
    agent = user_agent
    user_is_agent = False
    if agent == user_agent:
        user_is_agent = True
    event_list = agent.contributions()
    no_bucket = 0
    with_bucket = 0
    event_value = Decimal("0.0")
    claim_value = Decimal("0.0")
    outstanding_claims = Decimal("0.0")
    claim_distributions = Decimal("0.0")
    claim_distro_events = []
    event_types = {e.event_type for e in event_list}
    filter_form = EventTypeFilterForm(event_types=event_types, data=request.POST or None)
    paid_filter = "U"
    if request.method == "POST":
        if filter_form.is_valid():
            #import pdb; pdb.set_trace()
            data = filter_form.cleaned_data
            et_ids = data["event_types"]
            start = data["start_date"]
            end = data["end_date"]
            paid_filter = data["paid_filter"]
            if start:
                event_list = event_list.filter(event_date__gte=start)
            if end:
                event_list = event_list.filter(event_date__lte=end)
            #belt and suspenders: if no et_ids, form is not valid
            if et_ids:
                event_list = event_list.filter(event_type__id__in=et_ids)

    for event in event_list:
        if event.bucket_rule_for_context_agent():
            with_bucket += 1
        else:
            no_bucket += 1
        for claim in event.claims():
            claim_value += claim.original_value
            outstanding_claims += claim.value
            for de in claim.distribution_events():
                claim_distributions += de.value
                claim_distro_events.append(de.event)
    et = EventType.objects.get(name="Distribution")
    all_distro_evts = EconomicEvent.objects.filter(to_agent=agent, event_type=et)
    other_distro_evts = [d for d in all_distro_evts if d not in claim_distro_events]
    other_distributions = sum(de.quantity for de in other_distro_evts)
    #took off csv export for now
    #event_ids = ",".join([str(event.id) for event in event_list])

    if paid_filter == "U":
        event_list = list(event_list)
        for evnt in event_list:
            if evnt.owed_amount() == 0:
                    event_list.remove(evnt)

    paginator = Paginator(event_list, 25)
    page = request.GET.get('page')
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        events = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        events = paginator.page(paginator.num_pages)

    #import pdb; pdb.set_trace()
    return render(request, "work/my_history.html", {
        "agent": agent,
        "user_is_agent": user_is_agent,
        "events": events,
        "filter_form": filter_form,
        #"event_ids": event_ids,
        "no_bucket": no_bucket,
        "with_bucket": with_bucket,
        "claim_value": format(claim_value, ",.2f"),
        "outstanding_claims": format(outstanding_claims, ",.2f"),
        "claim_distributions": format(claim_distributions, ",.2f"),
        "other_distributions": format(other_distributions, ",.2f"),
        "help": get_help("my_history"),
    })

@login_required
def change_history_event(request, event_id):
    event = get_object_or_404(EconomicEvent, pk=event_id)
    page = request.GET.get("page")
    #import pdb; pdb.set_trace()
    event_form = event.change_form(data=request.POST or None)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        page = request.POST.get("page")
        if event_form.is_valid():
            event = event_form.save(commit=False)
            event.changed_by = request.user
            event.save()
        agent = event.from_agent
        #next = request.POST.get("next")
        if page:
            #if next:
            #    if next == "work-contributions":
            #        return HttpResponseRedirect('/%s/'
            #            % ('work/my-history', page))
            return HttpResponseRedirect('/%s/'
                % ('work/my-history', page))
        else:
            #if next:
            #    if next == "work-contributions":
            #        return HttpResponseRedirect('/%s/'
            #            % ('work/my-history'))
            return HttpResponseRedirect('/%s/'
                % ('work/my-history'))
    return render(request, "work/change_history_event.html", {
        "event_form": event_form,
        "page": page,
    })



def create_worktimer_context(
        request,
        process,
        agent,
        commitment):
    prev = ""
    today = datetime.date.today()
    #todo: will not now handle lack of commitment
    event = EconomicEvent(
        event_date=today,
        from_agent=agent,
        to_agent=process.default_agent(),
        process=process,
        context_agent=process.context_agent,
        quantity=Decimal("0"),
        is_contribution=True,
        created_by = request.user,
    )

    if commitment:
        event.commitment = commitment
        event.event_type = commitment.event_type
        event.resource_type = commitment.resource_type
        event.unit_of_quantity = commitment.resource_type.unit
        init = {
            "work_done": commitment.finished,
            "process_done": commitment.process.finished,
        }
        wb_form = WorkbookForm(initial=init)
        prev_events = commitment.fulfillment_events.filter(event_date__lt=today)
        if prev_events:
            prev_dur = sum(prev.quantity for prev in prev_events)
            unit = ""
            if commitment.unit_of_quantity:
                unit = commitment.unit_of_quantity.abbrev
            prev = " ".join([str(prev_dur), unit])
    else:
        wb_form = WorkbookForm()
    #if event.quantity > 0:
    event.save()
    others_working = []
    other_work_reqs = []
    wrqs = process.work_requirements()
    if wrqs.count() > 1:
        for wrq in wrqs:
            if wrq.from_agent != commitment.from_agent:
                if wrq.from_agent:
                    wrq.has_labnotes = wrq.agent_has_labnotes(wrq.from_agent)
                    others_working.append(wrq)
                else:
                    other_work_reqs.append(wrq)
    return {
        "commitment": commitment,
        "process": process,
        "wb_form": wb_form,
        "others_working": others_working,
        "other_work_reqs": other_work_reqs,
        "today": today,
        "prev": prev,
        "event": event,
        "help": get_help("work_timer"),
    }

@login_required
def work_timer(
        request,
        process_id,
        commitment_id=None):
    process = get_object_or_404(Process, id=process_id)
    agent = get_agent(request)
    ct = None
    if commitment_id:
        ct = get_object_or_404(Commitment, id=commitment_id)
        #if not request.user.is_superuser:
        #    if agent != ct.from_agent:
        #        return render(request, 'valueaccounting/no_permission.html')
    template_params = create_worktimer_context(
        request,
        process,
        agent,
        ct,
    )
    return render(request, "work/work_timer.html",
        template_params)

@login_required
def save_timed_work_now(request, event_id):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        event = get_object_or_404(EconomicEvent, id=event_id)
        form = WorkbookForm(instance=event, data=request.POST)
        if form.is_valid():
            data = form.cleaned_data
            event = form.save(commit=False)
            event.changed_by = request.user
            process = event.process
            event.save()
            if not process.started:
                process.started = event.event_date
                process.changed_by=request.user
                process.save()
            data = "ok"
        else:
            data = form.errors
        return HttpResponse(data, content_type="text/plain")

@login_required
def work_process_finished(request, process_id):
    #import pdb; pdb.set_trace()
    process = get_object_or_404(Process, pk=process_id)
    if not process.finished:
        process.finished = True
        process.save()
    else:
        if process.finished:
            process.finished = False
            process.save()
    return HttpResponseRedirect('/%s/%s/'
        % ('work/process-logging', process_id))



#    O R D E R   P L A N S

@login_required
def order_list(request):
    agent = get_agent(request)
    help = get_help("order_list")
    #import pdb; pdb.set_trace()
    projects = agent.managed_projects()

    return render(request, "work/order_list.html", {
        "projects": projects,
        "agent": agent,
        "help": help,
    })


@login_required
def order_plan(request, order_id):
    agent = get_agent(request)
    order = get_object_or_404(Order, pk=order_id)
    #import pdb; pdb.set_trace()
    coordinated_projects = agent.managed_projects()
    if order.provider not in coordinated_projects:
        return render(request, 'valueaccounting/no_permission.html')
    error_message = ""
    order_items = order.order_items()
    rts = None
    add_order_item_form = None
    if agent:
        if order.order_type == "customer":
            patterns = PatternUseCase.objects.filter(use_case__identifier='cust_orders')
            if patterns:
                pattern = patterns[0].pattern
            else:
                raise ValidationError("no Customer Order ProcessPattern")
            rts = pattern.all_resource_types()
        else:
            rts = ProcessPattern.objects.all_production_resource_types()
        if rts:
            add_order_item_form = AddOrderItemForm(resource_types=rts)
        #import pdb; pdb.set_trace()
        visited = set()
        for order_item in order_items:
            order_item.processes = order_item.unique_processes_for_order_item(visited)
            if order_item.is_workflow_order_item():
                #import pdb; pdb.set_trace()
                init = {'quantity': order_item.quantity,}
                order_item.resource_qty_form = ResourceQuantityForm(prefix=str(order_item.id), initial=init)
                init = {'context_agent': order_item.context_agent,}
                order_item.project_form = ProjectSelectionForm(prefix=str(order_item.id), initial=init)
                last_date = order_item.process.end_date
                next_date = last_date + datetime.timedelta(days=1)
                init = {"start_date": next_date, "end_date": next_date}
                order_item.add_process_form = WorkflowProcessForm(prefix=str(order_item.id), initial=init, order_item=order_item)
    return render(request, "work/order_plan.html", {
        "order": order,
        "agent": agent,
        "order_items": order_items,
        "add_order_item_form": add_order_item_form,
        "error_message": error_message,
    })


@login_required
def change_project_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    agent = get_agent(request)
    coordinated_projects = agent.managed_projects()
    if order.provider not in coordinated_projects:
        return render(request, 'valueaccounting/no_permission.html')
    #import pdb; pdb.set_trace()
    order_form = OrderChangeForm(instance=order, data=request.POST or None)
    if request.method == "POST":
        if order_form.is_valid():
            order = order_form.save()
            return HttpResponseRedirect('/%s/'
                % ('work/order-list'))

    return render(request, "work/change_project_order.html", {
        "order_form": order_form,
        "order": order,
        "next": next,
    })


@login_required
def plan_work(request, rand=0):
    #import pdb; pdb.set_trace()
    agent = get_agent(request)
    slots = []
    resource_types = []
    selected_pattern = None
    selected_context_agent = None
    pattern_form = PatternProdSelectionForm()
    #import pdb; pdb.set_trace()
    ca_form = ProjectSelectionFilteredForm(agent=agent)
    init = {"start_date": datetime.date.today(), "end_date": datetime.date.today()}
    process_form = DateAndNameForm(data=request.POST or None)
    #demand_form = OrderSelectionFilteredForm(data=request.POST or None)
    if request.method == "POST":
        input_resource_types = []
        input_process_types = []
        done_process = request.POST.get("create-process")
        add_another = request.POST.get("add-another")
        edit_process = request.POST.get("edit-process")
        get_related = request.POST.get("get-related")
        if get_related:
            #import pdb; pdb.set_trace()
            selected_pattern = ProcessPattern.objects.get(id=request.POST.get("pattern"))
            selected_context_agent = EconomicAgent.objects.get(id=request.POST.get("context_agent"))
            if selected_pattern:
                slots = selected_pattern.event_types()
                for slot in slots:
                    slot.resource_types = selected_pattern.get_resource_types(slot)
            process_form = DateAndNameForm(initial=init)
            #demand_form = OrderSelectionFilteredForm(provider=selected_context_agent)
        else:
            #import pdb; pdb.set_trace()
            rp = request.POST
            today = datetime.date.today()
            if process_form.is_valid():
                start_date = process_form.cleaned_data["start_date"]
                end_date = process_form.cleaned_data["end_date"]
                process_name = process_form.cleaned_data["process_name"]
            else:
                start_date = today
                end_date = today
            demand = None
            added_to_order = False
            #if demand_form.is_valid():
            #    demand = demand_form.cleaned_data["demand"]
            #    if demand:
            #        added_to_order = True
            produced_rts = []
            cited_rts = []
            consumed_rts = []
            used_rts = []
            work_rts = []
            #import pdb; pdb.set_trace()
            for key, value in dict(rp).iteritems():
                if "selected-context-agent" in key:
                    context_agent_id = key.split("~")[1]
                    selected_context_agent = EconomicAgent.objects.get(id=context_agent_id)
                    continue
                if "selected-pattern" in key:
                    pattern_id = key.split("~")[1]
                    selected_pattern = ProcessPattern.objects.get(id=pattern_id)
                    continue
                et = None
                action = ""
                try:
                    #import pdb; pdb.set_trace()
                    et_name = key.split("~")[0]
                    et = EventType.objects.get(name=et_name)
                    action = et.relationship
                except EventType.DoesNotExist:
                    pass
                if action == "consume":
                    consumed_id = int(value[0])
                    consumed_rt = EconomicResourceType.objects.get(id=consumed_id)
                    consumed_rts.append(consumed_rt)
                    continue
                if action == "use":
                    used_id = int(value[0])
                    used_rt = EconomicResourceType.objects.get(id=used_id)
                    used_rts.append(used_rt)
                    continue
                if action == "cite":
                    cited_id = int(value[0])
                    cited_rt = EconomicResourceType.objects.get(id=cited_id)
                    cited_rts.append(cited_rt)
                    continue
                if action == "out":
                    produced_id = int(value[0])
                    produced_rt = EconomicResourceType.objects.get(id=produced_id)
                    produced_rts.append(produced_rt)
                    continue
                if action == "work":
                    work_id = int(value[0])
                    work_rt = EconomicResourceType.objects.get(id=work_id)
                    work_rts.append(work_rt)
                    continue

            if rand:
                if not demand:
                    demand = Order(
                        order_type="rand",
                        order_date=today,
                        due_date=end_date,
                        provider=selected_context_agent,
                        created_by=request.user)
                    demand.save()
            if not process_name:
                process_name = "Make something"
                if produced_rts:
                    process_name = " ".join([
                        "Make",
                        produced_rts[0].name,
                    ])

            process = Process(
                name=process_name,
                end_date=end_date,
                start_date=start_date,
                process_pattern=selected_pattern,
                created_by=request.user,
                context_agent=selected_context_agent
            )
            process.save()

            #import pdb; pdb.set_trace()
            for rt in produced_rts:
                #import pdb; pdb.set_trace()
                resource_types.append(rt)
                et = selected_pattern.event_type_for_resource_type("out", rt)
                if et:
                    commitment = process.add_commitment(
                        resource_type= rt,
                        demand=demand,
                        quantity=Decimal("1"),
                        event_type=et,
                        unit=rt.unit,
                        description="",
                        user=request.user)
                    if rand:
                        if not added_to_order: #add to order feature removed, didn't work, no simple solution
                            commitment.order = demand
                            commitment.order_item = commitment
                            commitment.save()

            for rt in cited_rts:
                et = selected_pattern.event_type_for_resource_type("cite", rt)
                if et:
                    commitment = process.add_commitment(
                        resource_type= rt,
                        demand=demand,
                        order_item = process.order_item(),
                        quantity=Decimal("1"),
                        event_type=et,
                        unit=rt.unit,
                        description="",
                        user=request.user)
            for rt in used_rts:
                if rt not in resource_types:
                    resource_types.append(rt)
                    et = selected_pattern.event_type_for_resource_type("use", rt)
                    if et:
                        commitment = process.add_commitment(
                            resource_type= rt,
                            demand=demand,
                            order_item = process.order_item(),
                            quantity=Decimal("1"),
                            event_type=et,
                            unit=rt.unit,
                            description="",
                            user=request.user)

            for rt in consumed_rts:
                if rt not in resource_types:
                    resource_types.append(rt)
                    et = selected_pattern.event_type_for_resource_type("consume", rt)
                    if et:
                        commitment = process.add_commitment(
                            resource_type= rt,
                            demand=demand,
                            order_item = process.order_item(),
                            quantity=Decimal("1"),
                            event_type=et,
                            unit=rt.unit,
                            description="",
                            user=request.user)

            for rt in work_rts:
                #import pdb; pdb.set_trace()
                agent = None
                et = selected_pattern.event_type_for_resource_type("work", rt)
                if et:
                    work_commitment = process.add_commitment(
                        resource_type= rt,
                        demand=demand,
                        order_item = process.order_item(),
                        quantity=Decimal("1"),
                        event_type=et,
                        unit=rt.unit,
                        from_agent=agent,
                        description="",
                        user=request.user)
                    if notification:
                        #import pdb; pdb.set_trace()
                        if not work_commitment.from_agent:
                            agent = get_agent(request)
                            users = work_commitment.possible_work_users()
                            site_name = get_site_name()
                            if users:
                                notification.send(
                                    users,
                                    "valnet_new_task",
                                    {"resource_type": work_commitment.resource_type,
                                    "due_date": work_commitment.due_date,
                                    "hours": work_commitment.quantity,
                                    "unit": work_commitment.resource_type.unit,
                                    "description": work_commitment.description or "",
                                    "process": work_commitment.process,
                                    "creator": agent,
                                    "site_name": site_name,
                                    }
                                )

            if done_process:
                return HttpResponseRedirect('/%s/'
                    % ('work/order-list'))
            #if add_another:
            #    return HttpResponseRedirect('/%s/%s/'
            #        % ('work/plan-work', rand))
            if edit_process:
                return HttpResponseRedirect('/%s/%s/'
                    % ('work/process-logging', process.id))

    return render(request, "work/plan_work.html", {
        "slots": slots,
        "selected_pattern": selected_pattern,
        "selected_context_agent": selected_context_agent,
        "ca_form": ca_form,
        "pattern_form": pattern_form,
        "process_form": process_form,
        #"demand_form": demand_form,
        "rand": rand,
        "help": get_help("process_select"),
    })

def project_history(request, agent_id):
    #import pdb; pdb.set_trace()
    project = get_object_or_404(EconomicAgent, pk=agent_id)
    agent = get_agent(request)
    event_list = project.contribution_events()
    #event_list = project.all_events()
    agent_ids = {event.from_agent.id for event in event_list if event.from_agent}
    agents = EconomicAgent.objects.filter(id__in=agent_ids)
    filter_form = ProjectContributionsFilterForm(agents=agents, data=request.POST or None)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        if filter_form.is_valid():
            data = filter_form.cleaned_data
            #event_type = data["event_type"]
            from_agents = data["from_agents"]
            start = data["start_date"]
            end = data["end_date"]
            if from_agents:
                event_list = event_list.filter(from_agent__in=from_agents)
            if start:
                event_list = event_list.filter(event_date__gte=start)
            if end:
                event_list = event_list.filter(event_date__lte=end)
    event_ids = ",".join([str(event.id) for event in event_list])
    paginator = Paginator(event_list, 25)
    page = request.GET.get('page')
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        events = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        events = paginator.page(paginator.num_pages)

    return render(request, "work/project_history.html", {
        "project": project,
        "events": events,
        "filter_form": filter_form,
        "agent": agent,
        "event_ids": event_ids,
    })

@login_required
def project_history_csv(request):
    #import pdb; pdb.set_trace()
    event_ids = request.GET.get("event-ids")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=project-history.csv'
    writer = csv.writer(response)
    event_ids_split = event_ids.split(",")
    queryset = EconomicEvent.objects.filter(id__in=event_ids_split)
    opts = EconomicEvent._meta
    field_names = [field.name for field in opts.fields]
    writer.writerow(field_names)
    for obj in queryset:
        row = []
        for field in field_names:
            x = getattr(obj, field)
            try:
                x = x.encode('latin-1', 'replace')
            except AttributeError:
                pass
            row.append(x)
        writer.writerow(row)

    return response


@login_required
def order_delete_confirmation_work(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    agent = get_agent(request)
    coordinated_projects = agent.managed_projects()
    if order.provider not in coordinated_projects:
        return render(request, 'work/no_permission.html')
    pcs = order.producing_commitments()
    sked = []
    reqs = []
    work = []
    tools = []
    #import pdb; pdb.set_trace()
    next = "order-list"
    if pcs:
        visited_resources = set()
        for ct in pcs:
            #visited_resources.add(ct.resource_type)
            schedule_commitment(ct, sked, reqs, work, tools, visited_resources, 0)
        return render(request, 'work/order_delete_confirmation_work.html', {
            "order": order,
            "sked": sked,
            "reqs": reqs,
            "work": work,
            "tools": tools,
            "next": next,
        })
    else:
        commitments = Commitment.objects.filter(independent_demand=order)
        if commitments:
            for ct in commitments:
                sked.append(ct)
                if ct.process not in sked:
                    sked.append(ct.process)
            return render(request, 'work/order_delete_confirmation_work.html', {
                "order": order,
                "sked": sked,
                "reqs": reqs,
                "work": work,
                "tools": tools,
                "next": next,
            })
        else:
            order.delete()
            if next == "order-list":
                return HttpResponseRedirect('/%s/'
                    % ('work/order-list'))
            #if next == "closed_work_orders":
            #    return HttpResponseRedirect('/%s/'
            #        % ('work/closed-work-orders'))




#   I N V O I C E

@login_required
def invoice_number(request):
    agent = get_agent(request)
    invoice_numbers = InvoiceNumber.objects.filter(
        created_by=request.user)
    form = InvoiceNumberForm(agent=agent, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            data = form.cleaned_data
            member = data["member"]
            nbr = form.save(commit=False)
            idate = datetime.date.today()
            nbr.invoice_date = idate
            nbr.created_date = idate
            nbr.created_by = request.user
            nbr.save()

        return HttpResponseRedirect('/%s/'
            % ('work/invoice-number',))


    return render(request, "work/invoice_number.html", {
        "help": get_help("invoice_number"),
        "agent": agent,
        "form": form,
        "invoice_numbers": invoice_numbers,
    })
