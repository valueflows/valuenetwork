#
# Base class for all EconomicResource types
#
#

import graphene

class EconomicResourceCategory(graphene.Enum):
    NONE = None
    CURRENCY = "currency"
    INVENTORY = "inventory"

class EconomicResourceBase(graphene.Interface):
    id = graphene.String()
    resource_type = graphene.String(source='resource_type_name') # need to figure this out with VF gang
    tracking_identifier = graphene.String(source='tracking_identifier')
    image = graphene.String(source='image')
    numeric_value = graphene.Float(source='numeric_value') #need to implement as quantity-value with unit
    unit = graphene.String(source='unit')
    note = graphene.String(source='note')
