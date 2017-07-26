#
# Graphene schema for exposing ResourceTaxonomyItem model
#

import graphene

from valuenetwork.valueaccounting.models import EconomicResourceType
from valuenetwork.api.types.EconomicResource import ResourceTaxonomyItem, EconomicResourceProcessCategory
from valuenetwork.api.types.EconomicEvent import Action
from django.db.models import Q


class Query(graphene.AbstractType):

    # define input query params

    resource_taxonomy_item = graphene.Field(ResourceTaxonomyItem,
                                            id=graphene.Int())

    all_resource_taxonomy_items = graphene.List(ResourceTaxonomyItem)

    resource_taxonomy_items_by_process_category = graphene.List(ResourceTaxonomyItem,
                                                               category=EconomicResourceProcessCategory())

    resource_taxonomy_items_by_action = graphene.List(ResourceTaxonomyItem,
                                                      action=Action())

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

    def resolve_resource_taxonomy_items_by_process_category(self, args, context, info):
        cat = args.get('category')
        return EconomicResourceType.objects.filter(behavior=cat)

    def resolve_resource_taxonomy_items_by_action(self, args, context, info):
        action = args.get('action')
        if action == Action.WORK:
            return EconomicResourceType.objects.filter(behavior="work")
        if action == Action.USE:
            return EconomicResourceType.objects.filter(behavior="used")
        if action == Action.CONSUME:
            return EconomicResourceType.objects.filter(behavior="consumed")
        if action == Action.CITE:
            return EconomicResourceType.objects.filter(behavior="cited")
        if action == Action.PRODUCE:
            return EconomicResourceType.objects.filter(Q(behavior="produced")|Q(behavior="used")|Q(behavior="cited")|Q(behavior="consumed"))
        if action == Action.IMPROVE or action == Action.ACCEPT:
            return EconomicResourceType.objects.filter(Q(behavior="produced")|Q(behavior="used")|Q(behavior="cited")|Q(behavior="consumed"))
        return None
