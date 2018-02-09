#
# Graphene schema for exposing ResourceClassification model
#

import graphene

from valuenetwork.valueaccounting.models import EconomicResourceType
from valuenetwork.api.types.EconomicResource import ResourceClassification, EconomicResourceProcessCategory
from valuenetwork.api.types.EconomicEvent import Action
from django.db.models import Q


class Query(graphene.AbstractType):

    # define input query params

    resource_classification = graphene.Field(ResourceClassification,
                                            id=graphene.Int())

    all_resource_classifications = graphene.List(ResourceClassification)

    resource_classifications_by_process_category = graphene.List(ResourceClassification,
                                                               category=EconomicResourceProcessCategory())

    resource_classifications_by_action = graphene.List(ResourceClassification,
                                                      action=Action())

    # load single item

    def resolve_resource_classification(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            rt = EconomicResourceType.objects.get(pk=id)
            if rt:
                return rt
        return None

    # load all items

    def resolve_all_resource_classifications(self, args, context, info):
        return EconomicResourceType.objects.all()

    def resolve_resource_classifications_by_process_category(self, args, context, info):
        cat = args.get('category')
        return EconomicResourceType.objects.filter(behavior=cat)

    def resolve_resource_classifications_by_action(self, args, context, info):
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
