import datetime
from django.conf import settings
from django.contrib.auth import authenticate
import graphene

from valuenetwork.api.models import JwtAuthenticatedToken


class CreateToken(graphene.relay.ClientIDMutation):
    class Input:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    token = graphene.String()
    ok = graphene.Boolean()
    error = graphene.String()

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        username = input.get('username')
        password = input.get('password')
        user = authenticate(username=username, password=password)
        encoded = None
        error = None
        if user is not None:
            token = JwtAuthenticatedToken()
            token.since = datetime.datetime.now()
            token.user = user
            token.save()
            encoded = token.token
        else:
            error = 'Invalid credentials'
        return CreateToken(token=encoded, ok=error is None, error=error)


class DeleteToken(graphene.relay.ClientIDMutation):
    class Input:
        token = graphene.String(required=True)

    ok = graphene.Boolean()
    error = graphene.String()

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        token = input.get('token')

        error = None
        try:
            jwt_token = JwtAuthenticatedToken.from_token(token)
            jwt_token.delete()
        except Exception, e:
            error = e.message

        return DeleteToken(ok=error is None, error=error)
