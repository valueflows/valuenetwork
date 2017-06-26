#
# QuantityValue type def
#

import graphene
from . import QuantityValueBase
from graphene_django.types import DjangoObjectType
from valuenetwork.api.models import QuantityValue


class QuantityValue(DjangoObjectType):

    numeric_value = graphene.Float(source='numeric_value')
    unit = graphene.String(source='unit')

    class Meta:
        model = QuantityValue
        only_fields = ('numeric_value', 'unit')

