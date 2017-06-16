#
# Organisation resource typedef.
#

import graphene
from . import EconomicResourceBase
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import EconomicResource

class OrganizationResourceType(DjangoObjectType):

    id = graphene.String()

    class Meta:
        interfaces = (EconomicResourceBase.EconomicResourceBaseType, )
        model = EconomicResource
        only_fields = ('id', 'resource_type', 'tracking_identifier', 'numeric_value', 'unit')
