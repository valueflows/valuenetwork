#
# Graphene schema for exposing EconomicAgent and related models
#

#from django.core.exceptions import PermissionDenied

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicEvent as EconomicEventProxy, Process as ProcessProxy
from valuenetwork.api.schemas.helpers import *


class Action(graphene.Enum):
    NONE = None
    WORK = "work"
    CONSUME = "consume"
    USE = "use"
    CITE = "cite"
    PRODUCE = "produce"
    CHANGE = "change"
    

class EconomicEvent(DjangoObjectType):
    action = graphene.String(source='action')
    #process = DjangoObjectType(source='process')
    #provider = DjangoObjectType(source='provider')
    #receiver = DjangoObjectType(source='receiver')
    #scope = DjangoObjectType(source='scope')
    #affected_resource = graphene.DjangoObjectType(source='affected_resource')
    #affected_quantity = graphene.(source='affected_quantity')
    numeric_value = graphene.Float(source='numeric_value') #need to implement as quantity-value with unit
    unit = graphene.String(source='unit')
    start = graphene.String(source='start')
    note = graphene.String(source='note')

    class Meta:
        model = EconomicEventProxy
        only_fields = ('id')
    
