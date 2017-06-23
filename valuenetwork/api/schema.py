#
# Graphene master schema for Valuenetwork datatypes
#
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

import graphene
import jwt
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from graphene_django.debug import DjangoDebug
from django.conf import settings

import valuenetwork.api.schemas.Auth
import valuenetwork.api.schemas.Agent
import valuenetwork.api.schemas.AgentRelationship
import valuenetwork.api.schemas.AgentRelationshipRole
import valuenetwork.api.schemas.Organization
import valuenetwork.api.schemas.Person
import valuenetwork.api.schemas.EconomicResource
import valuenetwork.api.schemas.Process
import valuenetwork.api.schemas.EconomicEvent
from valuenetwork.api.schemas.helpers import hash_password


class ViewerQuery(
    valuenetwork.api.schemas.Agent.Query,
    valuenetwork.api.schemas.AgentRelationship.Query,
    valuenetwork.api.schemas.AgentRelationshipRole.Query,
    valuenetwork.api.schemas.Organization.Query,
    valuenetwork.api.schemas.Person.Query,
    valuenetwork.api.schemas.EconomicResource.Query,
    valuenetwork.api.schemas.Process.Query,
    valuenetwork.api.schemas.EconomicEvent.Query,
    graphene.ObjectType
):
    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', None)
        self.user = kwargs.pop('user', None)
        super(ViewerQuery, self).__init__(*args, **kwargs)


class Query(graphene.ObjectType):
    viewer = graphene.Field(ViewerQuery, token=graphene.String())
    debug = graphene.Field(DjangoDebug, name='__debug')

    def resolve_viewer(self, args, context, info):
        token_str = args.get('token')
        token = jwt.decode(token_str, settings.SECRET_KEY)
        user = User.objects.get_by_natural_key(token['username'])
        if token is not None and user is not None:
            if token['password'] != hash_password(user):
                raise PermissionDenied("Invalid password")
            return ViewerQuery(token=token, user=user)
        raise PermissionDenied('Cannot access this resource')


class Mutation(graphene.ObjectType):
    create_token = valuenetwork.api.schemas.Auth.CreateToken.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
