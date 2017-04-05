import datetime
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import PermissionDenied
import graphene
import jwt


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
        encoded = None
        if user is not None:
            token = jwt.encode({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'prev_login': user.last_login.isoformat() if user.last_login is not None else None,

                # special fields used in validation
                'exp': (datetime.datetime.now() + datetime.timedelta(7)),
                'iat': datetime.datetime.now(),
            }, settings.SECRET_KEY)
            encoded = token

            # :TODO: we should also update user last_login time here
        else:
            raise PermissionDenied('Invalid credentials')
        return CreateToken(token=encoded)
