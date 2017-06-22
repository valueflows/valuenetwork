#
# Base class for all Process types


import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import Process as ProcessProxy
#from valuenetwork.api.schemas.helpers import *

class Process(DjangoObjectType):
    planned_start = graphene.String(source='planned_start')
    planned_duration = graphene.String(source='planned_duration')
    is_finished = graphene.String(source='is_finished')
    note = graphene.String(source='note')

    class Meta:
        model = ProcessProxy
        only_fields = ('id', 'name')
