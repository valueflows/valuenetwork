#
# Graphene schema for exposing EconomicResource model
#
# @package: OCP
# @since:   2017-06-03
#

#from django.core.exceptions import PermissionDenied

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicResource as EconomicResourceProxy
from valuenetwork.api.schemas.helpers import *

from valuenetwork.api.types.EconomicResource import EconomicResource


class Query(graphene.AbstractType):

    # define input query params
    
    economic_resource = graphene.Field(EconomicResource,
                                       id=graphene.Int())

    all_economic_resources = graphene.List(EconomicResource)

    # load single resource

    def resolve_economic_resource(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            resource = EconomicResourceProxy.objects.get(pk=id)
            if resource:
                return resource
        return None   

    # load all resources

    def resolve_all_economic_resources(self, args, context, info):
        return EconomicResourceProxy.objects.all()

