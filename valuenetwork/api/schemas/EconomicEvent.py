#
# Graphene schema for exposing EconomicEvent
#

import graphene
#import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import EconomicEvent as EconomicEventProxy
from valuenetwork.api.types.EconomicEvent import EconomicEvent


class Query(graphene.AbstractType):

    # define input query params

    economic_event = graphene.Field(EconomicEvent,
                                    id=graphene.Int())

    all_economic_events = graphene.List(EconomicEvent)

    # resolvers

    def resolve_economic_event(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            event = EconomicEventProxy.objects.get(pk=id)
            if event:
                return event
        return None

    def resolve_all_economic_events(self, args, context, info):
        return EconomicEventProxy.objects.all()


    

