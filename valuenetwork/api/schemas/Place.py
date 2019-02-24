#
# Graphene schema for exposing Place model (also known as Location)
#

import graphene
from valuenetwork.valueaccounting.models import Location
from valuenetwork.api.types.Place import Place
from six import with_metaclass
from django.contrib.auth.models import User
from .Auth import AuthedInputMeta, AuthedMutation
from django.core.exceptions import PermissionDenied


class Query(graphene.AbstractType):

    place = graphene.Field(Place,
                           id=graphene.Int(),
                           address=graphene.String())

    all_places = graphene.List(Place)

    def resolve_place(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            place = Location.objects.get(pk=id)
            if place:
                return place
        address = args.get('address')
        if address is not None:
            place = Location.objects.get(address=address)
            if place:
                return place
        return None

    def resolve_all_places(self, args, context, info):
        return Location.objects.all()


class CreatePlace(AuthedMutation):
    class Input(with_metaclass(AuthedInputMeta)):
        name = graphene.String(required=True)
        address = graphene.String(required=True)
        latitude = graphene.Float(required=True)
        longitude = graphene.Float(required=True)
        note = graphene.String(required=False)

    place = graphene.Field(lambda: Place)

    @classmethod
    def mutate(cls, root, args, context, info):
        #import pdb; pdb.set_trace()
        name = args.get('name')
        address = args.get('address')
        latitude = args.get('latitude')
        note = args.get('note')
        longitude = args.get('longitude')

        if not note:
            note = ""
        place = Location(
            name=name,
            address=address,
            latitude=latitude,
            description=note,
            longitude=longitude,
        )

        #user_agent = AgentUser.objects.get(user=context.user).agent
        is_authorized = True #user_agent.is_authorized(object_to_mutate=place)
        if is_authorized:
            place.save()  
        else:
            raise PermissionDenied('User not authorized to perform this action.')

        return CreatePlace(place=place)

