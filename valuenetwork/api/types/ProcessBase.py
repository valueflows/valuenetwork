#
# Base class for all Process types


import graphene

class ProcessBase(graphene.Interface):
    id = graphene.String()
    name = graphene.String()
    planned_start = graphene.String(source='planned_start')
    planned_duration = graphene.String(source='planned_duration')
    is_finished = graphene.String(source='is_finished')
