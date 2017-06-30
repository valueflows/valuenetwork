#
# EconomicResource:
#

import graphene
from graphene_django.types import DjangoObjectType

import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import EconomicResource as EconomicResourceProxy
from valuenetwork.api.models import QuantityValue as QuantityValueProxy
from valuenetwork.api.types.QuantityValue import Unit, QuantityValue

class EconomicResourceCategory(graphene.Enum):
    NONE = None
    CURRENCY = "currency"
    INVENTORY = "inventory"


class EconomicResource(DjangoObjectType):  #graphene.Interface):
    resource_type = graphene.String(source='resource_type_name') # need to figure this out with VF gang
    tracking_identifier = graphene.String(source='tracking_identifier')
    image = graphene.String(source='image')
    #numeric_value = graphene.Float(source='numeric_value') #need to implement as quantity-value with unit
    #unit = graphene.Field(Unit)
    current_quantity = graphene.Field(QuantityValue)
    note = graphene.String(source='note')
    category = graphene.String(source='category')

    class Meta:
        model = EconomicResourceProxy
        only_fields = ('id')

    def resolve_unit(self, args, *rargs):
        return self.unit

    def resolve_current_quantity(self, args, *rargs):
        #import pdb; pdb.set_trace()
        return QuantityValueProxy(numeric_value=self.quantity, unit=self.unit)
