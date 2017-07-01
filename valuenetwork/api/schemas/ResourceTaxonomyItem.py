#
# Graphene schema for exposing ResourceTaxonomyItem model
#

import graphene

from valuenetwork.valueaccounting.models import EconomicResourceType
from valuenetwork.api.types.EconomicResource import ResourceTaxonomyItem


class Query(graphene.AbstractType):

    # define input query params

    resource_taxonomy_item = graphene.Field(ResourceTaxonomyItem,
                                            id=graphene.Int())

    all_resource_taxonomy_items = graphene.List(ResourceTaxonomyItem)

    # load single item

    def resolve_resource_taxonomy_item(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            rt = EconomicResourceType.objects.get(pk=id)
            if rt:
                return rt
        return None

    # load all items

    def resolve_all_resource_taxonomy_items(self, args, context, info):
        return EconomicResourceType.objects.all()
