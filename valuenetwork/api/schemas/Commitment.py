#
# Graphene schema for exposing Commitment
#

import graphene
#import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import Commitment as CommitmentProxy
from valuenetwork.api.types.Commitment import Commitment


class Query(graphene.AbstractType):

    # define input query params

    commitment = graphene.Field(Commitment,
                                    id=graphene.Int())

    all_commitments = graphene.List(Commitment)

    # resolvers

    def resolve_commitment(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            event = CommitmentProxy.objects.get(pk=id)
            if event:
                return event
        return None

    def resolve_all_commitments(self, args, context, info):
        return CommitmentProxy.objects.all()


    

