#
# Graphene schema for exposing EconomicResource model
#
# @package: OCP
# @since:   2017-06-03
#

#from django.core.exceptions import PermissionDenied

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicResource, EconomicAgent
from valuenetwork.api.schemas.helpers import *

# bind Django models to Graphene types

class EconomicResourceAPI(DjangoObjectType):
    resource_type = graphene.String(source='resource_type_name') # need to figure this out with VF gang
    tracking_identifier = graphene.String(source='tracking_identifier')
    image = graphene.String(source='image')
    numeric_value = graphene.Float(source='numeric_value')
    unit = graphene.String(source='unit')
    note = graphene.String(source='note')

    class Meta:
        model = EconomicResource
        only_fields = ('id')


# define public query API

class Query(graphene.AbstractType):

    # define input query params
    
    economic_resource = graphene.Field(EconomicResourceAPI,
                                       id=graphene.Int())

    all_economic_resources = graphene.List(EconomicResourceAPI)

    owned_economic_resources = graphene.List(EconomicResourceAPI,
                                             id=graphene.Int())

    owned_currency_economic_resources = graphene.List(EconomicResourceAPI,
                                                      id=graphene.Int())

    owned_inventory_economic_resources = graphene.List(EconomicResourceAPI,
                                                       id=graphene.Int())
    # load single resource

    def resolve_economic_resource(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            resource = EconomicResource.objects.get(pk=id)
            if resource:
                return resource
        return None   

    # load all resources

    def resolve_all_economic_resources(self, args, context, info):
        return EconomicResource.objects.all()

    # load resources owned by one agent

    def resolve_owned_economic_resources(self, args, context, info):
        id = args.get('id')
        if id is not None:
            agent = EconomicAgent.objects.get(pk=id)
            if agent:
                return agent.owned_resources()
        return None
    
    def resolve_owned_currency_economic_resources(self, args, context, info):
        id = args.get('id')
        if id is not None:
            agent = EconomicAgent.objects.get(pk=id)
            if agent:
                return agent.owned_currency_resources()
        return None
    
    def resolve_owned_inventory_economic_resources(self, args, context, info):
        id = args.get('id')
        if id is not None:
            agent = EconomicAgent.objects.get(pk=id)
            if agent:
                return agent.owned_inventory_resources()
        return None
