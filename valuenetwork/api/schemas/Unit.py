#
# Graphene schema for exposing Unit model
#

import graphene

from valuenetwork.api.types.QuantityValue import Unit
from valuenetwork.valueaccounting.models import Unit as UnitProxy, AgentUser
from six import with_metaclass
from django.contrib.auth.models import User
from .Auth import AuthedInputMeta, AuthedMutation
from django.core.exceptions import PermissionDenied


class Query(graphene.AbstractType):

    unit = graphene.Field(Unit,
                          id=graphene.Int())

    all_units = graphene.List(Unit)

    def resolve_unit(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            unit = UnitProxy.objects.get(pk=id)
            if unit:
                return unit
        return None

    # load all items

    def resolve_all_units(self, args, context, info):
        return UnitProxy.objects.all()


class CreateUnit(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        name = graphene.String(required=True)
        symbol = graphene.String(required=False)

    unit = graphene.Field(lambda: Unit)

    @classmethod
    def mutate(cls, root, args, context, info):
        #import pdb; pdb.set_trace()
        name = args.get('name')
        symbol = args.get('symbol')

        if not symbol:
            note = ""
        unit = UnitProxy(
            name=name,
            symbol=symbol
        )

        user_agent = AgentUser.objects.get(user=context.user).agent
        #is_authorized = user_agent.is_authorized(object_to_mutate=ResourceClassification)
        #if is_authorized:
        if user_agent:
            unit.save()  
        else:
           raise PermissionDenied('User not authorized to perform this action.')

        return CreateUnit(unit=unit)
