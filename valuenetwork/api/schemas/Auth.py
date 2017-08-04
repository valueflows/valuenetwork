from six import with_metaclass
import datetime
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
import graphene
from graphene.types.mutation import MutationMeta
from graphene.utils.is_base_type import is_base_type
import jwt
from .helpers import hash_password


class CreateToken(graphene.Mutation):
    class Input:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    token = graphene.String()

    @classmethod
    def mutate(cls, root, args, context, info):
        username = args.get('username')
        password = args.get('password')
        user = authenticate(username=username, password=password)
        hashed_passwd = hash_password(user)
        if user is not None:
            token = jwt.encode({
                'id': user.id,
                'username': user.username,
                'password': hashed_passwd,
                'iat': datetime.datetime.now(),
            }, settings.SECRET_KEY)
            encoded = token
        else:
            raise PermissionDenied('Invalid credentials')
        return CreateToken(token=encoded)


# Auth helper, metaclass & superclass for setting up mutations which require authentication (ie. most of them)
def _authUser(token_str):
    token = jwt.decode(token_str, settings.SECRET_KEY)
    user = User.objects.get_by_natural_key(token['username'])
    if token is not None and user is not None:
        if token['password'] != hash_password(user):
            raise PermissionDenied("Invalid credentials")
        return user
    raise PermissionDenied('Invalid credentials')   # purposefully generic error to guard against hack attempt info gathering

class _AuthedMutationMeta(MutationMeta):
    def __new__(cls, name, bases, attrs):
        if not is_base_type(bases, _AuthedMutationMeta):
            return type.__new__(cls, name, bases, attrs)

        cls.__orig_mutate = attrs['mutate'] # store original mutate method on the class
        del attrs['mutate'] # prevent it getting injected by MutationMeta as we want the overridden one in this class to be used

        return MutationMeta.__new__(cls, name, bases, attrs)

    @classmethod
    def mutate(cls, root, args, context, info):
        # authenticate automagically before running mutation, throw exception on bad credentials
        context.user = _authUser(args.get('token'))
        # now run the original mutation, exposing the user in the context object
        return cls.__orig_mutate(root, args, context, info)

class AuthedMutation(with_metaclass(_AuthedMutationMeta, graphene.ObjectType)):
    pass

class AuthedInputMeta(type):
    def __new__(mcs, classname, bases, dictionary):
        dictionary['token'] = graphene.String(required=True)
        return type.__new__(mcs, classname, bases, dictionary)
