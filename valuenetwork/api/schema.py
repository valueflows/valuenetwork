#
# Graphene master schema for Valuenetwork datatypes
#
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

import graphene
import jwt
from django.core.exceptions import PermissionDenied
from graphene_django.debug import DjangoDebug

import valuenetwork.api.schemas.Auth
import valuenetwork.api.schemas.EconomicAgent


class ViewerQuery(
    valuenetwork.api.schemas.EconomicAgent.Query,
    graphene.ObjectType
):
    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', None)
        super(ViewerQuery, self).__init__(*args, **kwargs)


class Query(graphene.ObjectType):
    viewer = graphene.Field(ViewerQuery, token=graphene.String())
    debug = graphene.Field(DjangoDebug, name='__debug')

    def resolve_viewer(self, args, context, info):
        token_str = args.get('token')
        token = jwt.decode(token_str)
        if token is not None:
            return ViewerQuery(token=token)
        raise PermissionDenied('Cannot access this resource')


class Mutation(graphene.ObjectType):
    create_token = valuenetwork.api.schemas.Auth.CreateToken.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
