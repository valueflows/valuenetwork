#
# EconomicResource:
#

import graphene
from graphene_django.types import DjangoObjectType
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from valuenetwork.api.schemas.Auth import _authUser
import datetime

import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import EconomicResource as EconomicResourceProxy, EconomicResourceType, Facet as FacetProxy, FacetValue as FacetValueProxy
from valuenetwork.api.models import QuantityValue as QuantityValueProxy, formatAgentList
from valuenetwork.api.types.QuantityValue import Unit, QuantityValue


class EconomicResourceCategory(graphene.Enum):
    NONE = None
    CURRENCY = "currency"
    INVENTORY = "inventory"
    WORK = "work"
    #SERVICE = "service" TODO: work this in, might need a new event type in VF


class EconomicResourceProcessCategory(graphene.Enum):
    NONE = None
    CONSUMED = "consumed"
    USED = "used"
    CITED = "cited"
    PRODUCED = "produced"


class Facet(DjangoObjectType):

    class Meta:
        model = FacetProxy
        only_fields = ('id', 'name', 'description')

    facet_values = graphene.List(lambda: FacetValue)
    
    def resolve_facet_values(self, args, context, info):
        return self.values.all()

class FacetValue(DjangoObjectType):
    facet = graphene.Field(lambda: types.Facet)

    class Meta:
        model = FacetValueProxy
        only_fields = ('id', 'value', 'description')


class ResourceClassification(DjangoObjectType):
    image = graphene.String(source='image')
    note = graphene.String(source='note')
    category = graphene.String(source='category')
    process_category = graphene.String(source='process_category')

    class Meta:
        model = EconomicResourceType
        only_fields = ('id', 'name', 'unit', 'context_agent')

    classification_resources = graphene.List(lambda: EconomicResource)

    classification_facets = graphene.List(lambda: Facet)

    classification_facet_values = graphene.List(lambda: FacetValue)

    generate_plan_from_workflow_recipe = graphene.Field(lambda: types.Plan)

    #classification_facet_values = graphene.List(lambda: FacetValue)

    def resolve_classification_resources(self, args, context, info):
        return self.resources.all()

    def resolve_classification_facets(self, args, context, info):
        rtfvs = self.facets.all()
        facets = []
        for rtfv in rtfvs:
            if rtfv.facet_value.facet not in facets:
                facets.append(rtfv.facet_value.facet)
        return facets

    def resolve_classification_facet_values(self, args, context, info):
        rtfvs = self.facets.all()
        fvs = []
        for rtfv in rtfvs:
            if rtfv.facet_value not in fvs:
                fvs.append(rtfv.facet_value)
        return fvs

    # This is a shameless hack!!!
    def resolve_generate_plan_from_workflow_recipe(self, args, context, *rargs):
        token = rargs[0].variable_values['token']
        context.user = _authUser(token)
        return self.generate_staged_work_order("Plan name", datetime.date.today(), context.user)

    #def resolve_classification_facet_values(self, args, context, info):
    #    return self.facets.all() #TODO in process, not working yet

class EconomicResource(DjangoObjectType):
    resource_classified_as = graphene.Field(ResourceClassification)
    tracking_identifier = graphene.String(source='tracking_identifier')
    image = graphene.String(source='image')
    current_quantity = graphene.Field(QuantityValue)
    note = graphene.String(source='note')
    category = graphene.String(source='category')
    current_location = graphene.Field(lambda: types.Place)
    created_date = graphene.String(source='created_date')

    class Meta:
        model = EconomicResourceProxy
        only_fields = ('id', 'url')

    transfers = graphene.List(lambda: types.Transfer)

    resource_contacts = graphene.List(lambda: types.Agent)
    
    owners = graphene.List(lambda: types.Agent)

    def resolve_current_quantity(self, args, *rargs):
        return QuantityValueProxy(numeric_value=self.quantity, unit=self.unit)

    def resolve_resource_classified_as(self, args, *rargs):
        return self.resource_type

    def resolve_current_location(self, args, *rargs):
        return self.current_location

    def resolve_transfers(self, args, context, info):
        return self.transfers()

    def resolve_resource_contacts(self, args, context, info):
        return formatAgentList(self.all_contact_agents())

    def resolve_owners(self, args, context, info):
        return formatAgentList(self.owners())
