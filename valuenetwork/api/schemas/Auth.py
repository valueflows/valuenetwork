import datetime
from django.conf import settings
from django.contrib.auth import authenticate
import graphene
import jwt


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
            token = jwt.encode({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'prev_login': user.last_login.isoformat(),

                # special fields used in validation
                'exp': (datetime.datetime.now() + datetime.timedelta(7)),
                'iat': datetime.datetime.now(),
            }, settings.SECRET_KEY)
            encoded = token

            # :TODO: we should also update user last_login time here
        else:
            error = 'Invalid credentials'
        return CreateToken(token=encoded, ok=error is None, error=error)
