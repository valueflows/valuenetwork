import datetime
import time
import csv
from operator import attrgetter

from django.db.models import Q
from django.http import Http404
from django.views.generic import list_detail
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.template import RequestContext
from django.http import HttpResponse
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import simplejson
from django.forms.models import formset_factory, modelformset_factory
from django.utils import simplejson

from valuenetwork.valueaccounting.models import *
from valuenetwork.valueaccounting.views import *
from valuenetwork.valueaccounting.forms import *
from valuenetwork.valueaccounting.utils import *

def projects(request):
    roots = Project.objects.filter(parent=None)
    
    return render_to_response("valueaccounting/projects.html", {
        "roots": roots,
    }, context_instance=RequestContext(request))

def contributions(request, project_id):
    #import pdb; pdb.set_trace()
    project = get_object_or_404(Project, pk=project_id)
    event_list = project.events.all()
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
    
    return render_to_response("valueaccounting/project_contributions.html", {
        "project": project,
        "events": events,
    }, context_instance=RequestContext(request))

def contribution_history(request, agent_id):
    #import pdb; pdb.set_trace()
    agent = get_object_or_404(EconomicAgent, pk=agent_id)
    event_list = agent.given_events.all()
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
    
    return render_to_response("valueaccounting/agent_contributions.html", {
        "agent": agent,
        "events": events,
    }, context_instance=RequestContext(request))


def log_time(request):
    nick = request.user.username
    if nick:
        try:
            member = EconomicAgent.objects.get(nick=nick.capitalize)
        except EconomicAgent.DoesNotExist:
            member = get_object_or_404(EconomicAgent, nick=nick)
    else:
        member = "Unregistered"
    form = TimeForm()
    roots = Project.objects.filter(parent=None)
    roles = Role.objects.all()
    return render_to_response("valueaccounting/log_time.html", {
        "member": member,
        "form": form,
        "roots": roots,
        "roles": roles,
    }, context_instance=RequestContext(request))


class EventSummary(object):
    def __init__(self, agent, role, quantity, value=Decimal('0.0')):
        self.agent = agent
        self.role = role
        self.quantity = quantity
        self.value=value

    def key(self):
        return "-".join([str(self.agent.id), str(self.role.id)])

    def quantity_formatted(self):
        return self.quantity.quantize(Decimal('.01'), rounding=ROUND_UP)


class AgentSummary(object):
    def __init__(self, 
        agent, 
        value=Decimal('0.0'), 
        percentage=Decimal('0.0'),
        amount=Decimal('0.0'),
    ):
        self.agent = agent
        self.value=value
        self.percentage=percentage
        self.amount=amount


def value_equation(request, project_id):
    project = get_object_or_404(Project, pk=project_id)    
    if not CachedEventSummary.objects.all().exists():
        summaries = CachedEventSummary.summarize_events(project)
    all_subs = project.with_all_sub_projects()
    summaries = CachedEventSummary.objects.select_related(
        'agent', 'project', 'role').filter(project__in=all_subs).order_by(
        'agent__name', 'project__name', 'role__name')
    total = 0
    agent_totals = []
    init = {"equation": "( hours * ( rate + importance + reputation ) ) + seniority"}
    form = EquationForm(data=request.POST or None,
        initial=init)
    if request.method == "POST":
        #import pdb; pdb.set_trace()
        if form.is_valid():
            data = form.cleaned_data
            equation = data["equation"]
            amount = data["amount"]
            if amount:
                amount = Decimal(amount)
            eq = equation.split(" ")
            for i, x in enumerate(eq):
                try:
                    y = Decimal(x)
                    eq[i] = "".join(["Decimal('", x, "')"])
                except InvalidOperation:
                    continue
            s = " "
            equation = s.join(eq)
            agent_sums = {}
            total = Decimal("0.00")
            safe_list = ['math',]
            safe_dict = dict([ (k, locals().get(k, None)) for k in safe_list ])
            safe_dict['Decimal'] = Decimal
            #import pdb; pdb.set_trace()
            for summary in summaries:
                safe_dict['hours'] = summary.quantity
                safe_dict['rate'] = summary.role_rate
                safe_dict['importance'] = summary.importance
                safe_dict['reputation'] = summary.reputation
                safe_dict['seniority'] = Decimal(summary.agent.seniority())
                #import pdb; pdb.set_trace()
                summary.value = eval(equation, {"__builtins__":None}, safe_dict)
                agent = summary.agent
                if not agent.id in agent_sums:
                    agent_sums[agent.id] = AgentSummary(agent)
                agent_sums[agent.id].value += summary.value
                total += summary.value
            agent_totals = agent_sums.values()
            #import pdb; pdb.set_trace()
            for at in agent_totals:
               pct = at.value / total
               at.value = at.value.quantize(Decimal('.01'), rounding=ROUND_UP)
               at.percentage = ( pct * 100).quantize(Decimal('.01'), rounding=ROUND_UP)
               if amount:
                   at.amount = (amount * pct).quantize(Decimal('.01'), rounding=ROUND_UP)

    paginator = Paginator(summaries, 50)
    page = request.GET.get('page')
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        events = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        events = paginator.page(paginator.num_pages)
    
    return render_to_response("valueaccounting/value_equation.html", {
        "project": project,
        "events": events,
        "form": form,
        "agent_totals": agent_totals,
        "total": total,
    }, context_instance=RequestContext(request))

def extended_bill(request, resource_type_id):
    rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    nodes = generate_xbill(rt)
    return render_to_response("valueaccounting/extended_bill.html", {
        "resource_type": rt,
        "nodes": nodes,
        "photo_size": (128, 128),
        "big_photo_size": (200, 200),
    }, context_instance=RequestContext(request))

def edit_extended_bill(request, resource_type_id):
    rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    nodes = generate_xbill(rt)
    resource_type_form = EconomicResourceTypeForm(instance=rt)
    process_form = XbillProcessTypeForm()
    change_process_form = ChangeProcessTypeForm()
    source_form = AgentResourceTypeForm()
    input_form = ProcessTypeResourceTypeForm()
    return render_to_response("valueaccounting/edit_xbill.html", {
        "resource_type": rt,
        "nodes": nodes,
        "photo_size": (128, 128),
        "big_photo_size": (200, 200),
        "resource_type_form": resource_type_form,
        "process_form": process_form,
        "change_process_form": change_process_form,
        "source_form": source_form,
        "input_form": input_form,
    }, context_instance=RequestContext(request))


def change_resource_type(request, resource_type_id):
    #import pdb; pdb.set_trace()
    if request.method == "POST":
        rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
        form = EconomicResourceTypeForm(request.POST, request.FILES, instance=rt)
        if form.is_valid():
            data = form.cleaned_data
            form.save()
            return HttpResponseRedirect('/%s/%s/'
                % ('accounting/edit-xbomfg', resource_type_id))

#todo: need error return here

def create_process_type_input(request):
    #import pdb; pdb.set_trace()
    process_type_id = request.POST.get("process_type_id")
    resource_type_id = request.POST.get("resource_type_id")
    relationship_id = request.POST.get("relationship_id")
    unit_id = request.POST.get("unit_id")
    quantity = request.POST.get("quantity")
    pt = get_object_or_404(ProcessType, pk=process_type_id)
    rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    rel = get_object_or_404(ResourceRelationship, pk=relationship_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    quantity = Decimal(quantity)
    ptrt = ProcessTypeResourceType(
        process_type=pt,
        resource_type=rt,
        relationship=rel,
        unit_of_quantity=unit,
        quantity=quantity,
    )
    ptrt.save()
    data = "ok"
    return HttpResponse(data, mimetype="text/plain")


def change_process_type_input(request):
    #import pdb; pdb.set_trace()
    process_type_resource_type_id = request.POST.get("process_type_resource_type_id")
    resource_type_id = request.POST.get("resource_type_id")
    relationship_id = request.POST.get("relationship_id")
    unit_id = request.POST.get("unit_id")
    quantity = request.POST.get("quantity")
    ptrt = get_object_or_404(ProcessTypeResourceType, pk=process_type_resource_type_id)
    rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    rel = get_object_or_404(ResourceRelationship, pk=relationship_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    quantity = Decimal(quantity)
    save_ptrt = False
    if ptrt.resource_type.id != rt.id:
        ptrt.resource_type = rt
        save_ptrt = True
    if ptrt.relationship.id != rel.id:
        ptrt.relationship = rel
        save_ptrt = True
    if ptrt.unit_of_quantity.id != unit.id:
        ptrt.unit_of_quantity = unit
        save_ptrt = True
    if ptrt.quantity != quantity:
        ptrt.quantity = quantity
        save_ptrt = True
    if save_ptrt:
        ptrt.save()
    data = "ok"
    return HttpResponse(data, mimetype="text/plain")

def change_agent_resource_type(request):
    #import pdb; pdb.set_trace()
    agent_id = request.POST.get("agent_id")
    agent_resource_type_id = request.POST.get("agent_resource_type_id")
    relationship_id = request.POST.get("relationship_id")
    unit_id = request.POST.get("unit_id")
    value = request.POST.get("value") or 0.0
    lead_time = request.POST.get("lead_time") or 0
    lead_time = int(lead_time)
    agt = get_object_or_404(EconomicAgent, pk=agent_id)
    art = get_object_or_404(AgentResourceType, pk=agent_resource_type_id)
    rel = get_object_or_404(ResourceRelationship, pk=relationship_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    value = Decimal(value)
    save_art = False
    if art.agent.id != agt.id:
        art.agent=agt
        save_art = True
    if art.relationship.id != rel.id:
        art.relationship=rel
        save_art = True
    if art.unit_of_value.id != unit.id:
        art.unit_of_value=unit
        save_art = True
    if art.lead_time != lead_time:
        art.lead_time=lead_time
        save_art = True
    if art.value != value:
        art.value=value
        save_art = Tru
    if save_art:
        art.save()
    data = "ok"
    return HttpResponse(data, mimetype="text/plain")


def create_agent_resource_type(request):
    #import pdb; pdb.set_trace()
    agent_id = request.POST.get("agent_id")
    resource_type_id = request.POST.get("resource_type_id")
    relationship_id = request.POST.get("relationship_id")
    unit_id = request.POST.get("unit_id")
    value = request.POST.get("value") or 0.0
    lead_time = request.POST.get("lead_time") or 0
    lead_time = int(lead_time)
    agt = get_object_or_404(EconomicAgent, pk=agent_id)
    rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    rel = get_object_or_404(ResourceRelationship, pk=relationship_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    value = Decimal(value)
    art = AgentResourceType(
        agent=agt,
        resource_type=rt,
        relationship=rel,
        lead_time=lead_time,
        unit_of_value=unit,
        value=value,
    )
    art.save()
    data = "ok"
    return HttpResponse(data, mimetype="text/plain")

def change_process_type(request):
    #import pdb; pdb.set_trace()
    process_type_id = request.POST.get("process_type_id")
    parent_id = request.POST.get("parent_id")
    name = request.POST.get("name")
    description = request.POST.get("description")
    url = request.POST.get("url")
    estimated_duration = request.POST.get("estimated_duration") or 0
    estimated_duration = int(estimated_duration)
    pt = get_object_or_404(ProcessType, pk=process_type_id)
    parent = None
    if parent_id:
        parent = get_object_or_404(ProcessType, pk=parent_id)
    save_pt = False
    if pt.name != name:
        pt.name=name
        save_pt = True
    if pt.parent:
        if pt.parent.id != parent_id:
            pt.parent=parent
            save_pt = True
    elif parent:
        pt.parent=parent
        save_pt = True
    if pt.description != description:
        pt.description=description
        save_pt = True
    if pt.url != url:
        pt.url=url
        save_pt = True
    if pt.estimated_duration != estimated_duration:
        pt.estimated_duration=estimated_duration
        save_pt = True
        estimated_duration=estimated_duration,
    if save_pt:
        pt.save()
    data = "ok"
    return HttpResponse(data, mimetype="text/plain")

def create_process_type_for_resource_type(request):
    #import pdb; pdb.set_trace()
    resource_type_id = request.POST.get("resource_type_id")
    parent_id = request.POST.get("parent_id")
    name = request.POST.get("name")
    description = request.POST.get("description")
    url = request.POST.get("url")
    estimated_duration = request.POST.get("estimated_duration") or 0
    estimated_duration = int(estimated_duration)
    unit_id = request.POST.get("unit_id")
    quantity = request.POST.get("quantity") or 0.0
    rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    parent = None
    if parent_id:
        parent = get_object_or_404(ProcessType, pk=parent_id)
    unit = None
    if unit_id:
        unit = get_object_or_404(Unit, pk=unit_id)
    quantity = Decimal(quantity)
    pt = ProcessType(
        name=name,
        parent=parent,
        description=description,
        url=url,
        estimated_duration=estimated_duration,
    )
    pt.save()
    #todo: hack based on rel name, which is user changeable
    rel = ResourceRelationship.objects.get(name="produces")
    ptrt = ProcessTypeResourceType(
        process_type=pt,
        resource_type=rt,
        relationship=rel,
        unit_of_quantity=unit,
        quantity=quantity,
    )
    ptrt.save()
    data = "ok"
    return HttpResponse(data, mimetype="text/plain")

def network(request, resource_type_id):
    #import pdb; pdb.set_trace()
    rt = get_object_or_404(EconomicResourceType, pk=resource_type_id)
    nodes, edges = graphify(rt, 3)
    return render_to_response("valueaccounting/network.html", {
        "resource_type": rt,
        "photo_size": (128, 128),
        "nodes": nodes,
        "edges": edges,
    }, context_instance=RequestContext(request))

def timeline(request):
    timeline_date = datetime.date.today().strftime("%b %e %Y 00:00:00 GMT-0600")
    unassigned = Commitment.objects.filter(from_agent=None).order_by("due_date")
    return render_to_response("valueaccounting/timeline.html", {
        "timeline_date": timeline_date,
        "unassigned": unassigned,
    }, context_instance=RequestContext(request))

def json_timeline(request):
    #data = "{ 'wiki-url':'http://simile.mit.edu/shelf/', 'wiki-section':'Simile JFK Timeline', 'dateTimeFormat': 'Gregorian','events': [{'start':'May 28 2006 09:00:00 GMT-0600','title': 'Writing Timeline documentation','link':'http://google.com','description':'Write some doc already','durationEvent':false }, {'start': 'Jun 16 2006 00:00:00 GMT-0600' ,'end':  'Jun 26 2006 00:00:00 GMT-0600' ,'durationEvent':true,'title':'Friends wedding'}]}"
    #import pdb; pdb.set_trace()
    processes = Process.objects.all()
    events = {'dateTimeFormat': 'Gregorian','events':[]}
    for process in processes:
        backshedule_events(process, events)
    data = simplejson.dumps(events, ensure_ascii=False)
    return HttpResponse(data, mimetype="text/json-comment-filtered")
