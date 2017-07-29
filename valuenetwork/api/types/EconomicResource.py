#
# EconomicResource:
#

import graphene
from graphene_django.types import DjangoObjectType

#import valuenetwork.api.types as types
from valuenetwork.valueaccounting.models import EconomicResource as EconomicResourceProxy, EconomicResourceType
from valuenetwork.api.models import QuantityValue as QuantityValueProxy
from valuenetwork.api.types.QuantityValue import Unit, QuantityValue

class EconomicResourceCategory(graphene.Enum):
    NONE = None
    CURRENCY = "currency"
    INVENTORY = "inventory"
    WORK = "work"

class EconomicResourceProcessCategory(graphene.Enum):
    NONE = None
    CONSUMED = "consumed"
    USED = "used"
    CITED = "cited"
    PRODUCED = "produced"

class ResourceTaxonomyItem(DjangoObjectType):
    image = graphene.String(source='image')
    note = graphene.String(source='note')
    category = graphene.String(source='category')
    process_category = graphene.String(source='process_category')

    class Meta:
        model = EconomicResourceType
        only_fields = ('id', 'name')

    taxonomy_item_resources = graphene.List(lambda: EconomicResource)

    def resolve_taxonomy_item_resources(self, args, context, info):
        return self.resources.all()


class EconomicResource(DjangoObjectType):
    resource_taxonomy_item = graphene.Field(ResourceTaxonomyItem)
    tracking_identifier = graphene.String(source='tracking_identifier')
    image = graphene.String(source='image')
    current_quantity = graphene.Field(QuantityValue)
    note = graphene.String(source='note')
    category = graphene.String(source='category')

    class Meta:
        model = EconomicResourceProxy
        only_fields = ('id')

    def resolve_current_quantity(self, args, *rargs):
        return QuantityValueProxy(numeric_value=self.quantity, unit=self.unit)

    def resolve_resource_taxonomy_item(self, args, *rargs):
        return self.resource_type
