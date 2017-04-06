#
# Helper functions for dealing with Graphene output
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

from django.core.exceptions import MultipleObjectsReturned
from django.conf import settings
import hashlib


def ensureSingleModel(result):
    if (result.count() != 1):
        raise MultipleObjectsReturned
    return result.first()

def hash_password(user):
    algo = hashlib.sha1()
    algo.update(user.password)
    algo.update(user.username)
    algo.update(settings.SECRET_KEY)
    return algo.hexdigest()
