from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import jwt


class JwtAuthenticatedToken(models.Model):
    user = models.ForeignKey(User)
    since = models.DateTimeField(auto_created=True)

    @property
    def token(self):
        return jwt.encode({
            'id': self.id,
            'username': self.user.username,
            'password': self.user.password,
            'since': self.since.strftime('%Y/%m/%d %H:%M:%S')
        }, settings.SECRET_KEY)

    @classmethod
    def from_token(cls, value):
        payload = jwt.decode(value, settings.SECRET_KEY)
        jwt_auth_token = JwtAuthenticatedToken.objects.filter(id=payload.get('id')).first()
        if jwt_auth_token is None:
            raise JwtAuthenticatedToken.DoesNotExist('Cannot find token by that ID')
        if jwt_auth_token.token == value:
            return jwt_auth_token
        raise ValueError('Invalid forged token')