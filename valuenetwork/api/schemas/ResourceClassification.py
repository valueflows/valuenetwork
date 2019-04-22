#
# Graphene schema for exposing ResourceClassification model
#

import graphene

from valuenetwork.valueaccounting.models import EconomicResourceType, Facet as FacetProxy, FacetValue as FacetValueProxy, Unit, AgentUser
from valuenetwork.api.types.EconomicResource import ResourceClassification, EconomicResourceProcessCategory, Facet, FacetValue
from valuenetwork.api.types.EconomicEvent import Action
from django.db.models import Q
from six import with_metaclass
from django.contrib.auth.models import User
from .Auth import AuthedInputMeta, AuthedMutation
from django.core.exceptions import PermissionDenied


class Query(graphene.AbstractType):

    # define input query params

    resource_classification = graphene.Field(ResourceClassification,
                                            id=graphene.Int())

    all_resource_classifications = graphene.List(ResourceClassification)

    resource_classifications_by_process_category = graphene.List(ResourceClassification,
                                                               category=EconomicResourceProcessCategory())

    resource_classifications_by_action = graphene.List(ResourceClassification,
                                                      action=Action())

    all_recipes = graphene.List(ResourceClassification)

    #returns resource classifications filtered by facet values in a string of comma delimited name:value, 
    #with some resource quantity > 0, for use in inventory filtering
    resource_classifications_by_facet_values = graphene.List(ResourceClassification,
                                                       facet_values=graphene.String())

    facet = graphene.Field(Facet,
                           id=graphene.Int())
 
    all_facets = graphene.List(Facet)


    def resolve_resource_classification(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            rt = EconomicResourceType.objects.get(pk=id)
            if rt:
                return rt
        return None

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

    def resolve_resource_classifications_by_facet_values(self, args, context, info):
        fvs = args.get('facet_values')
        return EconomicResourceType.objects.resource_types_by_facet_values(fvs)

    def resolve_facet(self, args, *rargs):
        id = args.get('id')
        if id:
            facet = FacetProxy.objects.get(pk=id)
            if facet:
                return facet
        return None

    def resolve_all_facets(self, args, context, info):
        return FacetProxy.objects.all()

    def resolve_all_recipes(self, args, context, info):
        return EconomicResourceType.objects.resource_types_with_recipes()


class CreateResourceClassification(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        name = graphene.String(required=True)
        note = graphene.String(required=False)
        image = graphene.String(required=False)
        category = graphene.String(required=False)
        unit = graphene.String(required=True)

    resourceClassification = graphene.Field(lambda: ResourceClassification)

    @classmethod
    def mutate(cls, root, args, context, info):
        #import pdb; pdb.set_trace()
        name = args.get('name')
        image = args.get('image')
        note = args.get('note')
        category = args.get('category')
        unit = args.get('unit')

        if not note:
            note = ""
        if not image:
            image = ""
        if category == "work":
            behavior = "work"
        elif category == "currency":
            behavior = "account"
        else:
            behavior = "other"
        #import pdb; pdb.set_trace()
        resourceClassification = EconomicResourceType(
            name=name,
            description=note,
            behavior=behavior,
            unit=Unit.objects.get(name=unit),
            photo_url=image,
            created_by=context.user,
        )

        user_agent = AgentUser.objects.get(user=context.user).agent
        #is_authorized = user_agent.is_authorized(object_to_mutate=ResourceClassification)
        #if is_authorized:
        if user_agent:
            resourceClassification.save()  
        else:
           raise PermissionDenied('User not authorized to perform this action.')

        return CreateResourceClassification(resourceClassification=resourceClassification)
