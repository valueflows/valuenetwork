#
# Graphene schema for exposing EconomicResource model
#

import graphene
from valuenetwork.valueaccounting.models import EconomicResource as EconomicResourceProxy
from valuenetwork.api.types.EconomicResource import EconomicResource


class Query(graphene.AbstractType):

    # define input query params

    economic_resource = graphene.Field(EconomicResource,
                                       id=graphene.Int())

    all_economic_resources = graphene.List(EconomicResource)

    # resolve methods

    def resolve_economic_resource(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            resource = EconomicResourceProxy.objects.get(pk=id)
            if resource:
                #resource.current_quantity = self._current_quantity(quantity=resource.quantity, unit=resource.unit)
                return resource
        return None   

    def resolve_all_economic_resources(self, args, context, info):
        resources = EconomicResourceProxy.objects.all()
        #for resource in resources:
            #resource.current_quantity = self._current_quantity(quantity=resource.quantity, unit=resource.unit)
        return resources
