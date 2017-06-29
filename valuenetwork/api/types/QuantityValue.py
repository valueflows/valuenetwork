#
# QuantityValue: A numeric amount and a unit, bundled.
#

import graphene
from graphene_django.types import DjangoObjectType
from valuenetwork.api.models import QuantityValue as QuantityValueProxy

#class Unit(DjangoObjectType):



class QuantityValue(DjangoObjectType):

    #numeric_value = graphene.Float(source='numeric_value')
    #unit = graphene.String(source='unit')

    class Meta:
        model = QuantityValueProxy
        only_fields = ('numeric_value', 'unit')
