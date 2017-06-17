#
# Organisation process typedef.
#

import graphene
from . import ProcessBase
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import Process

class OrganizationProcess(DjangoObjectType):

    id = graphene.String()

    class Meta:
        interfaces = (ProcessBase.ProcessBase, )
        model = Process
        only_fields = ('id', 'name')
