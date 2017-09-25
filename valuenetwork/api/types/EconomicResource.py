#
# EconomicResource:
#

import graphene
from graphene_django.types import DjangoObjectType

import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import EconomicResource as EconomicResourceProxy, EconomicResourceType
from valuenetwork.api.models import QuantityValue as QuantityValueProxy
from valuenetwork.api.types.QuantityValue import Unit, QuantityValue

class EconomicResourceCategory(graphene.Enum):
    NONE = None
    CURRENCY = "currency"
    INVENTORY = "inventory"
    WORK = "work"
    #SERVICE = "service" TODO: work this in, might need a new event type in VF

class EconomicResourceProcessCategory(graphene.Enum):
    NONE = None
    CONSUMED = "consumed"
    USED = "used"
    CITED = "cited"
    PRODUCED = "produced"

class ResourceClassification(DjangoObjectType):
    image = graphene.String(source='image')
    note = graphene.String(source='note')
    category = graphene.String(source='category')
    process_category = graphene.String(source='process_category')

    class Meta:
        model = EconomicResourceType
        only_fields = ('id', 'name')

    classification_resources = graphene.List(lambda: EconomicResource)

    def resolve_classification_resources(self, args, context, info):
        return self.resources.all()


class EconomicResource(DjangoObjectType):
    resource_classified_as = graphene.Field(ResourceClassification)
    tracking_identifier = graphene.String(source='tracking_identifier')
    image = graphene.String(source='image')
    current_quantity = graphene.Field(QuantityValue)
    note = graphene.String(source='note')
    category = graphene.String(source='category')
    #current_location

    class Meta:
        model = EconomicResourceProxy
        only_fields = ('id')

    transfers = graphene.List(lambda: types.Transfer)

    def resolve_current_quantity(self, args, *rargs):
        return QuantityValueProxy(numeric_value=self.quantity, unit=self.unit)

    def resolve_resource_classified_as(self, args, *rargs):
        return self.resource_type

    def resolve_transfers(self, args, context, info):
        return self.transfers()

