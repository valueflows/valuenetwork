#
# Helper functions for dealing with Graphene output
#
# @package: OCP
# @author:  pospi <pospi@spadgos.com>
# @since:   2017-03-20
#

from django.core.exceptions import MultipleObjectsReturned

def ensureSingleModel(result):
    if (result.count() != 1):
        raise MultipleObjectsReturned
    return result.first()
