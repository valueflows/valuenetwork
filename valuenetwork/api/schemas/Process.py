#
# Graphene schema for exposing Process model
#
# @package: OCP
# @since:   2017-06-22
#

#from django.core.exceptions import PermissionDenied

import graphene
from graphene_django.types import DjangoObjectType

from valuenetwork.valueaccounting.models import Process as ProcessProxy
from valuenetwork.api.schemas.helpers import *

from valuenetwork.api.types.Process import Process


class Query(graphene.AbstractType):

    # define input query params
    
    process = graphene.Field(Process,
                            id=graphene.Int())

    all_processes = graphene.List(Process)

    # load single item

    def resolve_process(self, args, *rargs):
        id = args.get('id')
        if id is not None:
            process = ProcessProxy.objects.get(pk=id)
            if process:
                return process
        return None   

    # load all items

    def resolve_all_processes(self, args, context, info):
        return ProcessProxy.objects.all()
