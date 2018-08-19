#
# Economic Event: An inflow or outflow of an economic resource in relation to a process and/or exchange. This could reflect a change in the quantity of a EconomicResource. It is also defined by its behavior in relation to the EconomicResource and a Process (consume, use, produce, etc.)" .
#

#from django.core.exceptions import PermissionDenied

import graphene
from graphene_django.types import DjangoObjectType
import valuenetwork.api.types as types
from valuenetwork.api.schemas.Auth import _authUser
from valuenetwork.api.types.QuantityValue import Unit, QuantityValue
from valuenetwork.valueaccounting.models import EconomicEvent as EconomicEventProxy, EconomicResource as EconomicResourceProxy, AgentUser
from valuenetwork.api.models import formatAgent, Person, Organization, QuantityValue as QuantityValueProxy
from valuenetwork.api.models import Fulfillment as FulfillmentProxy


class Action(graphene.Enum):
    NONE = None
    WORK = "work"
    CONSUME = "consume"
    USE = "use"
    CITE = "cite"
    PRODUCE = "produce"
    ACCEPT = "accept"
    IMPROVE = "improve"
    GIVE = "give"
    TAKE = "take"
    ADJUST = "adjust"


class EconomicEvent(DjangoObjectType):
    action = graphene.String(source='action')
    input_of = graphene.Field(lambda: types.Process)
    output_of = graphene.Field(lambda: types.Process)
    provider = graphene.Field(lambda: types.Agent)
    receiver = graphene.Field(lambda: types.Agent)
    scope = graphene.Field(lambda: types.Agent)
    affects = graphene.Field(lambda: types.EconomicResource)
    affected_quantity = graphene.Field(QuantityValue)
    start = graphene.String(source='start')
    url = graphene.String(source='url')
    request_distribution = graphene.Boolean(source='is_contribution')
    note = graphene.String(source='note')

    class Meta:
        model = EconomicEventProxy
        only_fields = ('id')

    fulfills = graphene.List(lambda: types.Fulfillment)

    user_is_authorized_to_update = graphene.Boolean()

    user_is_authorized_to_delete = graphene.Boolean()

    def resolve_input_of(self, args, *rargs):
        return self.input_of

    def resolve_output_of(self, args, *rargs):
        return self.output_of

    def resolve_provider(self, args, *rargs):
        return formatAgent(self.provider)

    def resolve_receiver(self, args, *rargs):
        return formatAgent(self.receiver)

    def resolve_scope(self, args, *rargs):
        return formatAgent(self.scope)

    #def resolve_affected_taxonomy_item(self, args, *rargs):
    #    return self.affected_taxonomy_item

    def resolve_affects(self, args, *rargs):
        res = self.affects
        if res == None:
            res = EconomicResourceProxy(resource_type=self.affected_resource_classified_as)
        return res

    def resolve_affected_quantity(self, args, *rargs):
        return QuantityValueProxy(numeric_value=self.quantity, unit=self.unit_of_quantity)

    # This is valid only for process related events, may need to re-look at when doing exchanges
    def resolve_fulfills(self, args, context, info):
        commitment = self.commitment
        if commitment:
            fulfillment = Fulfillment(
                fulfilled_by=self,
                fulfills=commitment,
                fulfilled_quantity=QuantityValueProxy(numeric_value=self.quantity, unit=self.unit_of_quantity),
                )
            ff_list = []
            ff_list.append(fulfillment)
            return ff_list
        return []

    def resolve_user_is_authorized_to_update(self, args, context, *rargs):
        token = rargs[0].variable_values['token']
        context.user = _authUser(token)
        user_agent = AgentUser.objects.get(user=context.user).agent
        return user_agent.is_authorized(object_to_mutate=self)

    def resolve_user_is_authorized_to_delete(self, args, context, *rargs):
        token = rargs[0].variable_values['token']
        context.user = _authUser(token)
        user_agent = AgentUser.objects.get(user=context.user).agent
        return user_agent.is_authorized(object_to_mutate=self)


class Fulfillment(DjangoObjectType):

    class Meta:
        model = FulfillmentProxy
        only_fields = ('id', 'fulfilled_by', 'fulfills', 'fulfilled_quantity', 'note')

