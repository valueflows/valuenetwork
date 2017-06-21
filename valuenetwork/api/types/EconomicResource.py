#
# Base class for all EconomicResource types
#
#

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicResource as EconomicResourceProxy
#from valuenetwork.api.schemas.helpers import *

class EconomicResourceCategory(graphene.Enum):
    NONE = None
    CURRENCY = "currency"
    INVENTORY = "inventory"

class EconomicResource(DjangoObjectType):  #graphene.Interface):
    resource_type = graphene.String(source='resource_type_name') # need to figure this out with VF gang
    tracking_identifier = graphene.String(source='tracking_identifier')
    image = graphene.String(source='image')
    numeric_value = graphene.Float(source='numeric_value') #need to implement as quantity-value with unit
    unit = graphene.String(source='unit')
    #quantity_value = 
    note = graphene.String(source='note')
    category = graphene.String(source='category')
    
    class Meta:
        model = EconomicResourceProxy
        only_fields = ('id')


