#
# Graphene master schema for Valuenetwork datatypes
#
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

import graphene
from graphene_django.debug import DjangoDebug

import valuenetwork.api.schemas.EconomicAgent

class Query(
    valuenetwork.api.schemas.EconomicAgent.Query,
    graphene.ObjectType):

    debug = graphene.Field(DjangoDebug, name='__debug')

    pass

schema = graphene.Schema(query=Query)
