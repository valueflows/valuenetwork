#
# Organisation process typedef.
#

import graphene
from . import ProcessBase
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import Process

class OrganizationProcessType(DjangoObjectType):

    id = graphene.String()

    class Meta:
        interfaces = (ProcessBase.ProcessBaseType, )
        model = Process
        only_fields = ('id', 'name')
