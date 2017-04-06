import datetime
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
import graphene
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
